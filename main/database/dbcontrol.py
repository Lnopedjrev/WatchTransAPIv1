import os
import bcrypt
import hashlib
from contextlib import contextmanager


class Model:

    def __init__(self, connection) -> None:
        self.connect = connection

    @contextmanager
    def _managed_cursor(self):
        cursor = self.connect.cursor()
        try:
            yield cursor
            self.connect.commit()
        except Exception as e:
            self.connect.rollback()
            raise MemoryError(f"Database operation error:{e}")
        finally:
            cursor.close


class Users(Model):

    def _create_new_user(self, email, password, jsonb_set, license_token=None):
        if self.fetch_user_by_email(email):
            raise ValueError("User already exists")
        hashed_password_bytes = self._password_encrypt(password)
        hashed_password = hashed_password_bytes.decode('utf-8')
        license_token = self._generate_token() if not license_token else license_token
        with self._managed_cursor() as cursor:
            create_user_command = """
                INSERT INTO Users(email, license_token, password, languages_list)
                    VALUES (%s, %s, %s, %s)
                """
            cursor.execute(create_user_command,
                           (email, license_token, hashed_password, jsonb_set))
        return license_token

    def fetch_user_by_email(self, email):
        with self._managed_cursor() as cursor:
            fetch_by_email_command = """
                    SELECT user_id, email, license_token, password FROM Users
                        WHERE email = %s
                    """
            cursor.execute(fetch_by_email_command, (email,))
            user_info = cursor.fetchone()
            if user_info:
                return {"user_id": user_info[0], "email": user_info[1],
                        "license_token": user_info[2], "password": user_info[3]}
            else:
                return False

    def user_authenticate(self, email, password):
        user = self.fetch_user_by_email(email)
        if user:
            hashed_password = user['password'].encode("utf-8")
            valid_password = bcrypt.checkpw(password, hashed_password)
            return {'user_id': user['user_id'], 'email': user['email']}, valid_password
        else:
            raise ValueError("User not found")
        # Make custom Errors

    def get_languages_list(self, user_id):
        with self._managed_cursor() as cursor:
            get_languages_command = """
                SELECT jsonb_object_keys(languages_list -> 'learn_languages') as lang_list
                FROM Users

                WHERE user_id=%s
                """
            cursor.execute(get_languages_command, (user_id,))
            lang_list = cursor.fetchall()
            return [lang[0] for lang in lang_list]

    def get_language_pairs(self, user_id):
        with self._managed_cursor() as cursor:
            get_language_pairs_comm = """
            SELECT jsonb_object_keys(languages_list -> 'learn_languages') as learn_lang, nat_Lang
            FROM Users
            CROSS JOIN jsonb_array_elements(languages_list -> 'native_language') as nat_lang
            WHERE user_id=%s
            """
            cursor.execute(get_language_pairs_comm, (user_id,))
            lang_pairs = cursor.fetchall()
            lang_pairs_list = ['-'.join([lang_pair[0], lang_pair[1]]) for lang_pair in lang_pairs]
            return lang_pairs_list

    def get_user_lang_level(self, user_id, lang):
        with self._managed_cursor() as cursor:
            get_level_command = """SELECT languages_list -> 'learn_languages' -> %s ->> 'level'
                                   FROM Users
                                   WHERE user_id = %s
                                """
            cursor.execute(get_level_command, (lang, user_id))
            lang_level = cursor.fetchone()
            return lang_level[0]

    def update_new_user(self, email, password, jsonb_set):
        with self._managed_cursor() as cursor:
            update_command = """UPDATE users
                                SET (password, languages_list) = (%s, %s)
                                WHERE email = %s"""
            hashed_password_bytes = self._password_encrypt(password)
            hashed_password = hashed_password_bytes.decode('utf-8')
            cursor.execute(update_command, (hashed_password, jsonb_set, email))
            return True

    @staticmethod
    def _password_encrypt(password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed

    @staticmethod
    def _generate_token():
        return hashlib.sha256(os.urandom(64)).hexdigest()


class LanguagePairs(Model):

    def create_new_language_pair(self, lang1, lang2):
        language_pair_name = self.get_language_pair_name(lang1, lang2)
        if self.get_language_pair_id(language_pair_name):
            raise ValueError
        with self._managed_cursor() as cursor:
            create_pair_command = """
                INSERT INTO Languages(language_pair_name)
                VALUES (%s)
            """
            cursor.execute(create_pair_command, (language_pair_name,))

    def get_language_pair_id(self, lang_pair_name):
        with self._managed_cursor() as cursor:
            search_command = """SELECT language_pair_id 
                                FROM Language_Pairs
                                WHERE language_pair_name=%s"""
            cursor.execute(search_command, (lang_pair_name,))
            lang_pair = cursor.fetchone()
            if not lang_pair:
                try:
                    self.add_language_pair_id(lang_pair_name)
                    cursor.execute(search_command, (lang_pair_name,))
                    lang_pair = cursor.fetchone()
                except Exception as e:
                    raise ValueError(e)
            return lang_pair[0]

    def add_language_pair_id(self, lang_pair_name):
        with self._managed_cursor() as cursor:
            lang1, lang2 = lang_pair_name.split('-')
            lang1_id = self.check_lang(lang1)
            lang2_id = self.check_lang(lang2)
            add_command = """INSERT INTO language_pairs(language_from, language_to, language_pair_name)
                             VALUES (%s, %s, %s)"""
            cursor.execute(add_command, (lang1_id, lang2_id, lang_pair_name))

    def check_lang(self, lang_name):
        with self._managed_cursor() as cursor:
            search_command = """SELECT language_id
                                FROM Languages
                                WHERE language_code = %s"""
            cursor.execute(search_command, (lang_name,))
            return cursor.fetchone()[0]

    def get_level_list(self, language_code, level):
        with self._managed_cursor() as cursor:
            fetch_command = """
                            WITH user_level_representation AS (
                                SELECT (levels -> %s ->> 'num_representation')::integer as num_repr 
                                FROM languages
                                WHERE language_code = %s
                            )

                            SELECT jsonb_array_elements(word_l) from (
                               SELECT key,
                                      (levels -> key ->> 'num_representation')::integer as num_r,
                                      levels -> key -> 'word_list' as word_l
                               FROM languages,
                                    jsonb_each(levels)
                               WHERE language_code = %s
                            ) as subquery
                            WHERE num_r <= (select num_repr from user_level_representation)
            """
            cursor.execute(fetch_command,
                           (level, language_code, language_code))
            level_list = cursor.fetchall()
            level_list = [word[0] for word in level_list]
            return level_list

    @staticmethod
    def get_language_pair_name(lang1, lang2):
        return lang1.upper() + "-" + lang2.upper()


class Words(Model):

    def add_new_word(self, user, language_pair, word, translation, source=None):
        if self.check_word_exist(user, word, language_pair):
            raise ValueError("Word already exists")
        with self._managed_cursor() as cursor:
            add_content_command = """
            INSERT INTO Words(user_id, language_pair_id, content,
                            content_translated, source)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(add_content_command, (user, language_pair, word,
                                                 translation, source))

    def retrieve_words_lang_pair(self, user, language_pair):
        with self._managed_cursor() as cursor:
            retrive_content_command = """
            SELECT content, content_translated, source
            FROM Words
            WHERE user_id = %s and language_pair_id = %s
            """
            cursor.execute(retrive_content_command, (user, language_pair))
            return cursor.fetchall()

    def retrieve_words_source(self, source):
        with self._managed_cursor() as cursor:
            cursor.execute("""SELECT content, content_tranlated, source
                                    FROM Words
                                    WHERE source = %s """,
                           (source,))
            return self.fetchone()

    def retrieve_words_today(self, user_id):
        with self._managed_cursor() as cursor:
            retrive_words_today = """
            SELECT content, content_translated, source, date_trunc('second', time_created) as "Time Added", language_pair_id
            FROM Words
            WHERE user_id = %s and time_created::date = CURRENT_DATE;
            """
            cursor.execute(retrive_words_today, (user_id,))
            return cursor.fetchall()

    def check_word_exist(self, user, word, language_pair):
        with self._managed_cursor() as cursor:
            check_command = """SELECT EXISTS(SELECT 1 FROM Words where (user_id = %s and content=%s) and language_pair_id=%s)"""
            cursor.execute(check_command, (user, word, language_pair))
            return cursor.fetchone()[0]
