from telebot import TeleBot, types
import random
from db_utils import (
    get_connection,
    register_user,
    get_random_word,
    get_wrong_options,
    add_user_word,
    delete_user_word
)


TOKEN = 'ВАШ ТОКЕН'
bot = TeleBot(TOKEN)

user_states = {}
new_word_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    conn = get_connection()
    register_user(message.from_user.id, message.from_user.username, conn)

    conn.close()

    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Начнем тренировку.")
    ask_question(message.chat.id, message.from_user.id)

def ask_question(chat_id, user_id):
    conn = get_connection()
    random_word = get_random_word(user_id, conn)
    if not random_word:
        bot.send_message(chat_id, "Словарь пуст. Добавьте слова.")
        conn.close()
        return
    w_id, rus, eng = random_word
    options = get_wrong_options(eng, user_id, conn) + [eng]
    random.shuffle(options)
    conn.close()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*[types.KeyboardButton(o) for o in options])
    markup.row(types.KeyboardButton("Дальше ⏭"), types.KeyboardButton("Добавить слово ➕"))
    markup.row(types.KeyboardButton("Удалить слово"))
    bot.send_message(chat_id, f"Выбери перевод слова:\n🇷🇺 {rus}", reply_markup=markup)
    user_states[chat_id] = {'rus': rus, 'eng': eng, 'user_id': user_id}

@bot.message_handler(func=lambda m: m.text == "Дальше ⏭")
def next_q(m): ask_question(m.chat.id, m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "Добавить слово ➕")
def add_w(m):
    bot.send_message(m.chat.id, "Введите русское слово:")
    new_word_state[m.chat.id] = {'state': 'waiting_rus'}

@bot.message_handler(func=lambda m: new_word_state.get(m.chat.id, {}).get('state') == 'waiting_rus')
def rus_in(m):
    new_word_state[m.chat.id].update({'rus_word': m.text.lower(), 'state': 'waiting_eng'})
    bot.send_message(m.chat.id, "Введите перевод:")

@bot.message_handler(func=lambda m: new_word_state.get(m.chat.id, {}).get('state') == 'waiting_eng')
def eng_in(m):
    conn = get_connection()
    add_user_word(m.from_user.id, new_word_state[m.chat.id]['rus_word'], m.text.lower(), conn)
    conn.close()
    bot.send_message(m.chat.id, "Добавлено!")
    del new_word_state[m.chat.id]
    ask_question(m.chat.id, m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "Удалить слово")
def del_w(m):
    bot.send_message(m.chat.id, "Что удалить?")
    new_word_state[m.chat.id] = {'state': 'waiting_delete'}

@bot.message_handler(func=lambda m: new_word_state.get(m.chat.id, {}).get('state') == 'waiting_delete')
def del_confirm(m):
    conn = get_connection()
    if delete_user_word(m.from_user.id, m.text.lower(), conn):
        bot.send_message(m.chat.id, "Удалено!")
    else:
        bot.send_message(m.chat.id, "Не найдено.")
    conn.close()
    del new_word_state[m.chat.id]
    ask_question(m.chat.id, m.from_user.id)

@bot.message_handler(func=lambda m: True)
def check(m):
    state = user_states.get(m.chat.id)
    if state and m.text.strip() == state['eng']:
        bot.send_message(m.chat.id, f"Отлично! ❤️\n{state['eng']} -> {state['rus']}")
        ask_question(m.chat.id, m.from_user.id)
    else:
        bot.send_message(m.chat.id, "😕 Неправильно, еще раз!")

if __name__ == '__main__':
    bot.polling(non_stop=True)