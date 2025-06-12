CREATE TABLE IF NOT EXISTS Users(
        user_id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        license_token VARCHAR(255) UNIQUE,
        password VARCHAR(255),
        languages_list JSONB
    );

CREATE TABLE IF NOT EXISTS Languages(
        language_code VARCHAR(10) UNIQUE NOT NULL,
        language_id SERIAL PRIMARY KEY,
        levels JSONB
    );

CREATE TABLE IF NOT EXISTS Language_Pairs(
        language_from INTEGER REFERENCES Languages(language_id) ON DELETE CASCADE,
        language_to INTEGER REFERENCES Languages(language_id) ON DELETE CASCADE,
        language_pair_id SERIAL PRIMARY KEY,
        language_pair_name VARCHAR(255) UNIQUE
    );

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

CREATE TABLE IF NOT EXISTS Tokens(
        token VARCHAR(255) UNIQUE;
        email VARCHAR(255) UNIQUE;
);

CREATE OR REPLACE FUNCTION create_partitions(num_partitions INT) 
RETURNS VOID
language plpgsql
as $$
DECLARE
	i INT;
BEGIN 
	FOR i in 0..(num_partitions - 1) LOOP
		EXECUTE format('
			CREATE TABLE Words_part_%s
			PARTITION OF Words
			FOR VALUES WITH (MODULUS %s, REMAINDER %s);					   
		', i, num_partitions, i);
	END LOOP;
END;
$$;

-- INSERT INTO Languages(language_code) VALUES ('EN'), ('RU'), ('DE');

SELECT create_partitions(4);


INSERT INTO Languages(language_code) VALUES ('EN'), ('RU'), ('DE'), ('KZ');
