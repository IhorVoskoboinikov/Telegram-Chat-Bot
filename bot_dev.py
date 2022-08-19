# -*- coding: utf-8 -*-
import threading
import time
import schedule
import telebot
import messages
from telebot import types
import peewee
import pandas as pd
import datetime
from datetime import timedelta
from collections import defaultdict
import calendar

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read()

bot = telebot.TeleBot(TOKEN)
database = peewee.SqliteDatabase("clients.db")
_client_choice = []
_club_card_to_save = defaultdict(dict)
_users_buy_card = {}
_names_of_trainings_set = set()
_trainings_by_date = {}
_trainings_to_records = defaultdict(list)


class BaseTable(peewee.Model):
    class Meta:
        database = database


class ClubCards(BaseTable):
    user_id = peewee.IntegerField()
    name = peewee.CharField()
    title = peewee.CharField()
    validity = peewee.IntegerField()
    price = peewee.IntegerField()
    date_of_buy = peewee.DateTimeField()
    date_of_the_end = peewee.DateTimeField()


ClubCards.create_table()


def user_name(first_name, last_name):  # функция проверки и присвоения имени пользователя
    user_name = f'{first_name} {last_name}'
    if not last_name:
        user_name = f'{first_name}'
    return user_name


def user_cards_in_db(user_id):  # функция проверки наличия абонементов в базе
    _user_club_cards = messages.USER_NO_ACCOUNT_MESSAGE
    for clients in ClubCards.select():
        if user_id == clients.user_id:
            _user_club_cards = f'У Вас есть действующий абонемент - {clients.title}\n' \
                               f'Дата покупки: {clients.date_of_buy}\n' \
                               f'Срок действия до: {clients.date_of_the_end}\n' \
                               f'Стоимость: {clients.price} грн.'
    return _user_club_cards


def push_messages():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    contact_the_manager = types.KeyboardButton('Связаться с менеджером')
    markup.add(contact_the_manager)
    for clients in ClubCards.select():
        today = datetime.datetime.now()
        date_of_end_three_days = datetime.datetime.strptime(clients.date_of_the_end, '%d.%m.%Y')
        if today.day == (date_of_end_three_days - (timedelta(3))).day:
            mess = f'{clients.name} {messages.PUSH_MESSAGE_END_OF_THE_CARD} {clients.date_of_the_end}!'
            bot.send_message(chat_id=clients.user_id, text=mess, disable_notification=True, reply_markup=markup)


@bot.message_handler(commands=['start'])  # старт работы бота
def start(message):
    _user_name = user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = user_cards_in_db(user_id=message.from_user.id)
    mess = f'{_user_name}, {messages.GREETING_MESSAGE}'
    sticker = open('images/hello_sticker.webp', 'rb')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем главное меню
    general_information = types.KeyboardButton('Общая информация')
    clubs_card = types.KeyboardButton('Клубные карты')
    sign_up_for_a_workout = types.KeyboardButton('Записаться на тренировку')
    working_hours = types.KeyboardButton('Время работы клуба')
    contact_the_manager = types.KeyboardButton('Связаться с менеджером')
    markup.add(general_information, clubs_card, sign_up_for_a_workout, working_hours, contact_the_manager)
    bot.send_sticker(message.chat.id, sticker)
    bot.send_message(message.chat.id, mess, reply_markup=markup)


@bot.message_handler(content_types=['text'])  # обработка текстовых запросов от пользователя
def get_user_text(message):
    global _users_buy_card, _names_of_trainings_set
    _user_name = user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = user_cards_in_db(user_id=message.from_user.id)
    df = pd.read_excel('base_cards.xlsx')  # чтение абонементов из Excel заполняются менеджером
    df_tr = pd.read_excel('trainings.xlsx')  # чтение абонементов из Excel заполняются менеджером
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if message.text in ['Общая информация', 'Время работы клуба', 'Связаться с менеджером']:
        restart = '/start'
        markup.add(restart)
        bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')

    elif message.text == 'Записаться на тренировку':
        mess = messages.CHOICE_TRAININGS_MESSAGE
        _names_of_trainings_set = set((i.title) for i in df_tr.itertuples())
        for y in _names_of_trainings_set:
            trainings = types.KeyboardButton(y)
            markup.add(trainings)
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif message.text in _names_of_trainings_set:
        for i in df_tr.itertuples():
            if message.text == i.title:
                training = types.KeyboardButton(f'{i.title}: {i.day_of_the_week} '
                                                f'в {i.time.strftime("%H:%M")}')
                markup.add(training)

        mess = messages.CHOICE_TRAININGS_MESSAGE_2
        bot.send_message(message.chat.id, mess, reply_markup=markup)

    elif message.text == 'Клубные карты':  # меню клубных карт для покупки клиента
        _client_choice.clear()
        mess = f"{_user_club_cards}\n\n{messages.CHOICE_CLUB_CARD_MESSAGE}"
        for i in df.itertuples():
            abon_from_manadger = types.KeyboardButton(f"{i.title}: Срок-{i.validity} дней, цена-{i.price} грн")
            markup.add(abon_from_manadger)
            _client_choice.append(f"{i.title}: Срок-{i.validity} дней, цена-{i.price} грн")
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif message.text in _client_choice:  # подтверждение о покупке
        _users_buy_card[message.from_user.id] = message.text
        restart = '/start'
        i_agree = 'Купить абонемент'
        markup.add(restart, i_agree)
        mess = f'{_user_name}, {messages.CONFIRMATION_CLUB_CARD_IN_DB_MESSAGE}'
        if _user_club_cards == messages.USER_NO_ACCOUNT_MESSAGE:
            mess = f'{_user_name}, {messages.CONFIRMATION_CLUB_CARD_OUT_IN_DB_MESSAGE}'
        bot.send_message(message.chat.id, mess, reply_markup=markup)

    elif message.text == 'Купить абонемент':
        user_id_to_dict = str(message.from_user.id)
        restart = '/start'
        markup.add(restart)
        sticker = open('images/final_sticker.webp', 'rb')
        for clients in ClubCards.select():  # удаление действующих абонементов из базы
            if message.from_user.id == clients.user_id:
                clients.delete_instance()
        for i in df.itertuples():
            if i.title in _users_buy_card[message.from_user.id]:  # создание данных для записи в базу
                date = datetime.datetime.now()
                date_end = date + (timedelta(i.validity))
                _club_card_to_save[user_id_to_dict]['user_id'] = message.from_user.id
                _club_card_to_save[user_id_to_dict]['name'] = _user_name
                _club_card_to_save[user_id_to_dict]['title'] = i.title
                _club_card_to_save[user_id_to_dict]['validity'] = i.validity
                _club_card_to_save[user_id_to_dict]['price'] = i.price
                _club_card_to_save[user_id_to_dict]['date_of_buy'] = date.strftime("%d.%m.%Y")
                _club_card_to_save[user_id_to_dict]['date_of_the_end'] = date_end.strftime("%d.%m.%Y")
        mess = f'{_user_name}, спасибо за Ваш выбор!\n' \
               f'Ваш абонемент - {_club_card_to_save[user_id_to_dict]["title"]}\n' \
               f'Стоимость - {_club_card_to_save[user_id_to_dict]["price"]} грн.\n' \
               f'Дата покупки - {_club_card_to_save[user_id_to_dict]["date_of_buy"]}\n' \
               f'Действует до - {_club_card_to_save[user_id_to_dict]["date_of_the_end"]}\n\n' \
               f'Для перехода в главное меню нажмите кнопку start!'
        bot.send_sticker(message.chat.id, sticker)
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        client_in_db = ClubCards.insert_many(
            _club_card_to_save[user_id_to_dict]).execute()  # запись купленного абонемента в базу
        del _users_buy_card[message.from_user.id]
        del _club_card_to_save[user_id_to_dict]
        for clients in ClubCards.select():  # чтение данных из базы
            print(f'ID: {clients.user_id} | Имя: {clients.name} | '
                  f'Абонемент: {clients.title} | Срок: {clients.validity} | '
                  f'Стоимость:{clients.price} | Дата покупки: {clients.date_of_buy} | '
                  f'Действует до: {clients.date_of_the_end}')

    else:
        restart = '/start'
        markup.add(restart)
        bot.send_message(message.chat.id, messages.CHOICE_ERROR_MESSAGE, reply_markup=markup)


def run_bot():
    bot.polling(none_stop=True)


def run_push_message():
    schedule.every().day.at("06:00").do(push_messages)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    chat_bot = threading.Thread(target=run_bot)
    push_mess = threading.Thread(target=run_push_message)
    chat_bot.start()
    push_mess.start()
