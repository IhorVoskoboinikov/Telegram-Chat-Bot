import telebot
from text_responses import *
from telebot import types
import peewee
import pandas as pd

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read()

excel_data = pd.read_excel('base_cards.xlsx')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Привет, {message.from_user.first_name} {message.from_user.last_name}! \n' \
           f'Это фитнес клуб "Tsarsky City Resort "!\n\n' \
           f'Мы рады что ты выбрал именно нас для улучшения своей физической формы!\n\n' \
           f'Мы готовы ответить на все твои вопросы, выбери раздел:'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    general_information = types.KeyboardButton('Общая информация')
    clubs_card = types.KeyboardButton('Клубные карты')
    sign_up_for_a_workout = types.KeyboardButton('Записаться на тренировку')
    working_hours = types.KeyboardButton('Время работы клуба')
    contact_the_manager = types.KeyboardButton('Связаться с менеджером')
    markup.add(general_information, clubs_card, sign_up_for_a_workout, working_hours, contact_the_manager)
    # bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_message(message.chat.id, mess, reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_user_text(message):
    if message.text in ['Общая информация', 'Записаться на тренировку', 'Время работы клуба',
                        'Связаться с менеджером']:
        bot.send_message(message.chat.id, text_responses[message.text], parse_mode='html')
    elif message.text == 'Клубные карты':
        bot.send_message(message.chat.id, excel_data, parse_mode='html')
    else:
        bot.send_message(message.chat.id, 'Нужно выбрать из перечисленный вариантов!', parse_mode='html')


bot.polling(none_stop=True)

database = peewee.SqliteDatabase("club_cards.db")


class BaseTable(peewee.Model):
    class Meta:
        database = database


class ClubCards(BaseTable):
    title = peewee.CharField()
    validity = peewee.CharField()
    price = peewee.CharField()


ClubCards.create_table()
