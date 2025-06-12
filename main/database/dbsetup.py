import psycopg2
import dotenv
import os


dotenv.load_dotenv()
ENV_PATH = os.getenv('SECRET_FILE')
print(ENV_PATH)
dotenv.load_dotenv(dotenv_path=ENV_PATH)


def establish_connect():
    # print(os.getenv("PGDATABASE_NAME"))
    connection = psycopg2.connect(database=os.getenv("PGDATABASE_NAME"),
                                  user=os.getenv("PGDATABASE_USERNAME"),
                                  password=os.getenv("PGDATABASE_PASSWORD"),
                                  host=os.getenv("PGDATABASE_HOST"))
                                #   port=os.getenv("PGDATABASE_PORT"))
    return connection


def initial_setup(connection):
    table1 = """
    CREATE TABLE IF NOT EXISTS Users(
        user_id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        license_token VARCHAR(255) UNIQUE,
        password VARCHAR(255),
        languages_list JSONB
    );"""

    table2 = """
    CREATE TABLE IF NOT EXISTS Languages(
        language_code VARCHAR(10) UNIQUE NOT NULL,
        language_id SERIAL PRIMARY KEY,
        levels JSONB
    );"""

    table3 = """
    CREATE TABLE IF NOT EXISTS Language_Pairs(
        language_from INTEGER REFERENCES Languages(language_id) ON DELETE CASCADE,
        language_to INTEGER REFERENCES Languages(language_id) ON DELETE CASCADE,
        language_pair_id SERIAL PRIMARY KEY,
        language_pair_name VARCHAR(255) UNIQUE
    );"""

    table4 = """
    CREATE TABLE IF NOT EXISTS Words(
        word_id SERIAL,
        user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
        language_pair_id INTEGER REFERENCES Language_Pairs(language_pair_id) ON DELETE CASCADE,
        content VARCHAR(255) NOT NULL,
        content_translated VARCHAR(255) NOT NULL,
        source VARCHAR(255),
        time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (word_id, user_id)
    ) PARTITION BY HASH (user_id);
    """

    table5 = """
    CREATE TABLE IF NOT EXISTS TokensJWT(
        jti VARCHAR(36) PRIMARY KEY,
        subject INTEGER REFERENCES Users(user_id) ON DELETE CASCADE,
        revoked BOOLEAN,
        device_id VARCHAR(36) UNIQUE,
        expired_time TIMESTAMP
    )
    """

    cursor = connection.cursor()
    cursor.execute(table1)
    cursor.execute(table2)
    cursor.execute(table3)
    cursor.execute(table4)
    # cursor.execute(table5)
    connection.commit()


def dbmain():
    connection = establish_connect()
    # initial_setup(connection)
    return connection
