import telebot
from telebot import types

bot = telebot.TeleBot('2125399793:AAFWEjDTdXVPkerpBXp4JzMuTwNWKeURTYU')


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Привет, <b>{message.from_user.first_name} {message.from_user.last_name}</b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.message_handler(content_types=['text'])
def get_user_text(message):
    if message.text == 'Привет':
        bot.send_message(message.chat.id, 'И тебе привет', parse_mode='html')
    elif message.text == 'id':
        bot.send_message(message.chat.id, f'Твой ID: {message.from_user.id} ', parse_mode='html')
    elif message.text == 'photo':
        photo = open('like_icon.jpg', 'rb')
        bot.send_photo(message.chat.id, photo)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю)))', parse_mode='html')


@bot.message_handler(content_types=['photo'])
def get_user_photo(message):
    bot.send_message(message.chat.id, f'{message.from_user.last_name}, классное фото!')


@bot.message_handler(commands=['website'])
def website(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Жми на меня!', url='https://www.youtube.com'))
    bot.send_message(message.chat.id, f'{message.from_user.last_name}, перейди на youtube!', reply_markup=markup)


@bot.message_handler(commands=['help'])
def website(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    website = types.KeyboardButton('/website')
    start = types.KeyboardButton('/start')
    markup.add(website, start)
    bot.send_message(message.chat.id, 'OK', reply_markup=markup)


bot.polling(none_stop=True)





