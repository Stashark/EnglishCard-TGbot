import psycopg2



def get_connection():
    return psycopg2.connect(
        host='host',
        database='database',
        user='user',
        password='password',
        port='5432'
    )

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user_words CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS Words CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS Users CASCADE;")
    with open('tables.sql', 'r', encoding='utf-8') as sql_file:
        sql_script = sql_file.read()
    cursor.execute(sql_script)
    conn.commit()
    cursor.close()

def register_user(telegram_id, username, conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM Users WHERE telegram_id = %s", (telegram_id,))
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO Users (telegram_id, username) "
                        "VALUES (%s, %s)", (telegram_id, username))

            cur.execute("SELECT id FROM Words "
                        "WHERE is_common = TRUE")

            common_words = cur.fetchall()

            for (word_id,) in common_words:
                cur.execute("INSERT INTO user_words (user_id, word_id) "
                            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (telegram_id, word_id))
            conn.commit()

def get_random_word(telegram_id, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.id, w.rus_words, w.eng_words FROM Words w
            JOIN user_words uw ON w.id = uw.word_id
            WHERE uw.user_id = %s ORDER BY RANDOM() LIMIT 1
        """, (telegram_id,))
        return cur.fetchone()

def get_wrong_options(correct_eng_word, telegram_id, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.eng_words FROM Words w
            JOIN user_words uw ON w.id = uw.word_id
            WHERE uw.user_id = %s AND w.eng_words != %s ORDER BY RANDOM() LIMIT 3
        """, (telegram_id, correct_eng_word))
        options = [row[0] for row in cur.fetchall()]

        if len(options) < 3:
            needed = 3 - len(options)
            cur.execute("SELECT eng_words FROM Words "
                        "WHERE is_common = TRUE AND eng_words != %s "
                        "ORDER BY RANDOM() LIMIT %s", (correct_eng_word, needed))
            options.extend([row[0] for row in cur.fetchall()])
        return options

def add_user_word(telegram_id, rus_word, eng_word, conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO Words (rus_words, eng_words, is_common) "
                    "VALUES (%s, %s, FALSE) RETURNING id", (rus_word, eng_word))

        word_id = cur.fetchone()[0]

        cur.execute("INSERT INTO user_words (user_id, word_id) "
                    "VALUES (%s, %s) ON CONFLICT DO NOTHING", (telegram_id, word_id))
    conn.commit()

def delete_user_word(telegram_id, word_text, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w.id FROM Words w JOIN user_words uw ON w.id = uw.word_id
            WHERE uw.user_id = %s 
            AND (w.rus_words = %s OR w.eng_words = %s) LIMIT 1
        """, (telegram_id, word_text, word_text))

        word = cur.fetchone()

        if word:
            cur.execute("DELETE FROM user_words "
                        "WHERE user_id = %s AND word_id = %s", (telegram_id, word[0]))
            conn.commit()
            return True
        return False