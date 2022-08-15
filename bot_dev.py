import telebot
from text_responses import *
from telebot import types
import peewee
import pandas as pd

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read()

bot = telebot.TeleBot(TOKEN)
database = peewee.SqliteDatabase("clients.db")
_client_choice = []
_club_card_to_save = {}


class BaseTable(peewee.Model):
    class Meta:
        database = database


class ClubCards(BaseTable):
    name = peewee.CharField()
    title = peewee.CharField()
    validity = peewee.IntegerField()
    price = peewee.IntegerField()


ClubCards.create_table()


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
    # print(_client_choice)
    df = pd.read_excel('base_cards.xlsx')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if message.text in ['Общая информация', 'Записаться на тренировку', 'Время работы клуба',
                        'Связаться с менеджером']:
        bot.send_message(message.chat.id, text_responses[message.text], parse_mode='html')
    elif message.text == 'Клубные карты':
        _client_choice.clear()
        mess = "Выберите подходящий вам абонемент из ниже перечисленных:"
        for i in df.itertuples():
            mess = "Выберите подходящий вам абонемент из ниже перечисленных:"
            abon_from_manadger = types.KeyboardButton(f"{i.title}: Срок-{i.validity} дней, цена-{i.price} грн")
            markup.add(abon_from_manadger)
            _client_choice.append(f"{i.title}: Срок-{i.validity} дней, цена-{i.price} грн")
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif message.text in _client_choice:
        print(message.text)
        for i in df.itertuples():
            if i.title in message.text:
                _club_card_to_save['name'] = f'{message.from_user.first_name} {message.from_user.last_name}'
                _club_card_to_save['title'] = i.title
                _club_card_to_save['validity'] = i.validity
                _club_card_to_save['price'] = i.price
        restart = '/start'
        markup.add(restart)
        mess = f'{message.from_user.last_name}, спасибо за ваш выбор!\n' \
               f'Ваш абонемент - {message.text}!\n' \
               f'Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        print(_club_card_to_save)
        client_in_db = ClubCards.insert_many(_club_card_to_save).execute()
        for clients in ClubCards.select():
            print(f'Имя: {clients.name} Абонемент: {clients.title} Срок: {clients.validity} Стоимость:{clients.price}')
    else:
        restart = '/start'
        markup.add(restart)
        mess = 'Выбор можно делать только по перечисленным вариантам. Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)



bot.polling(none_stop=True)
