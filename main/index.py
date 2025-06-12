import os
import logging
from flask import Flask, render_template, request, jsonify
from database.dbsetup import dbmain
from database.dbcontrol import Words, Users, LanguagePairs
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from logapp.logInit import setup_logger


load_dotenv()
ENV_PATH = os.getenv('SECRET_FILE')
load_dotenv(dotenv_path=ENV_PATH)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
setup_logger()
apiLogger = logging.getLogger('apiLogger')
jwt = JWTManager(app)
connection = dbmain()


@app.route("/", methods=["POST", "GET"])
def index():

    return jsonify({
        "message": "hello"
    })


@app.route("/add_words", methods=["POST"])
@jwt_required(refresh=False)
def add_words():
    try:
        data = request.json
        words = data["words"]
        lang_id = data["lang_id"]
        user_id = data["user_id"]
        source = data["source"]
        words_db = Words(connection)
        for word in words:
            translation = words[word]
            words_db.add_new_word(user_id, lang_id,
                                  word, translation,
                                  source)
        return jsonify(), 201
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/get_langp_id", methods=["GET"])
def get_langp_id():
    try:
        args = request.args.to_dict()
        languages_db = LanguagePairs(connection)
        result = languages_db.get_language_pair_id(args['lang_pair'])
        return jsonify({
            "lang_pair_id": result
        })
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/authenticate", methods=['GET'])
@jwt_required()
def authenticate():
    try:
        email = get_jwt_identity()
        users_db = Users(connection)
        user = users_db.fetch_user_by_email(email)
        lang_pair_list = users_db.get_language_pairs(user['user_id'])
        return jsonify(
            user=user,
            lang_list=lang_pair_list
        )
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/refresh", methods=['POST'])
@jwt_required(refresh=True)
def access_refresh():
    try:
        email = get_jwt_identity()
        access_token = create_access_token(identity=email)
        return jsonify(
            access_token=access_token
        )
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/login", methods=['POST'])
def login():
    try:
        data = request.json
        email = data['email']

        password = data['password']
        password = password.encode("utf-8")

        users_db = Users(connection)

        user, validation = users_db.user_authenticate(email, password)

        if validation:
            lang_pair_list = users_db.get_language_pairs(user['user_id'])
            access_token = create_access_token(identity=email)
            refresh_token = create_refresh_token(identity=email)
            return jsonify({
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "lang_list": lang_pair_list
            })
        else:
            return jsonify(), 401
    except ValueError:
        return jsonify(), 401
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500

@app.route("/get_lvl_list", methods=["GET"])
def get_lvl_list():
    try:
        args = request.args.to_dict()
        language_pair = args['lang_pair']
        user_id = args['user_id']

        languages_db = LanguagePairs(connection)
        users_db = Users(connection)

        lang_from = language_pair.split("-")[0]
        lang_level = users_db.get_user_lang_level(user_id, lang_from)
        lang_level_words = languages_db.get_level_list(lang_from, lang_level)
        return jsonify({
            "lang_level_list": lang_level_words
        })
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/get_user_words", methods=["GET"])
@jwt_required()
def get_uwords():
    try:
        args = request.args.to_dict()
        language_pair = args['lang_pair']
        user_id = args['user_id']

        languages_db = LanguagePairs(connection)
        users_db = Users(connection)
        words_db = Words(connection)

        lang_from = language_pair.split("-")[0]
        lang_level = users_db.get_user_lang_level(user_id, lang_from)
        lang_level_words = languages_db.get_level_list(lang_from, lang_level)

        lang_pid = languages_db.get_language_pair_id(language_pair)
        db_words = words_db.retrieve_words_lang_pair(user_id, lang_pid)
        db_words = [word_row[0] for word_row in db_words]

        words = db_words + lang_level_words

        return jsonify({
            "words": words
        })
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/get_twords", methods=["GET"])
@jwt_required()
def get_today_words():
    try:
        args = request.args.to_dict()
        user_id = args['user_id']
        words_db = Words(connection)
        result = words_db.retrieve_words_today(user_id)
        return jsonify({
            "words": result
        })
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/new_user_reg", methods=["POST"])
def reg_user():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        jsonb_set = data['jbs']
        token = data['token']
        users_db = Users(connection)
        users_db._create_new_user(email, password, jsonb_set, token)
        return jsonify({
            "msg": "Success"
        })
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


@app.route("/logging", methods=['POST'])
def log_msg():
    try:
        data = request.json

        level = data['levelname']
        msg = data['message']

        match level:
            case 'ERROR':
                apiLogger.error(msg)
            case 'CRITICAL':
                apiLogger.critical(msg)
            case 'WARNING':
                apiLogger.warning(msg)
            case _:
                return jsonify(), 400

        return jsonify(), 204
    except Exception as e:
        apiLogger.error(e)
        return jsonify(), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)