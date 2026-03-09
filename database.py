from db_utils import get_connection, create_tables


def add_word(rus_word, eng_word, conn, is_common=True):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM Words WHERE rus_words = %s AND eng_words = %s", (rus_word, eng_word))
        if not cur.fetchone():
            cur.execute("INSERT INTO Words (rus_words, eng_words, is_common) VALUES (%s, %s, %s)",
                        (rus_word, eng_word, is_common))
            conn.commit()

if __name__ == "__main__":
    conn = get_connection()
    create_tables(conn)

    initial_words = [
        ('красный', 'red'), ('синий', 'blue'), ('зеленый', 'green'),
        ('желтый', 'yellow'), ('черный', 'black'), ('белый', 'white'),
        ('я', 'I'), ('ты', 'you'), ('он', 'he'), ('она', 'she')
    ]

    for rus_word, eng_word in initial_words:
        add_word(rus_word, eng_word, conn, True)

    print("База данных успешно заполнена!")
    conn.close()