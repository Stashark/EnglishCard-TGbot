CREATE TABLE IF NOT EXISTS Users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Words (
    id SERIAL PRIMARY KEY,
    rus_words VARCHAR(50),
    eng_words VARCHAR(50),
    is_common BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS user_words (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES Users(telegram_id) ON DELETE CASCADE,
    word_id INTEGER NOT NULL REFERENCES Words(id) ON DELETE CASCADE,
    UNIQUE(user_id, word_id)
);
