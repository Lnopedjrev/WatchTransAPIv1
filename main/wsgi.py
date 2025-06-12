from logapp.logInit import setup_logger
from index import app
from dotenv import load_dotenv
# from flask_jwt_extended import JWTManager


if __name__ == "__main__":
    # connection = dbmain()
    load_dotenv()
    app.run()