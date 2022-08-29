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
import re
import calendar
from pandas.io.excel import ExcelWriter
import os

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read()

bot = telebot.TeleBot(TOKEN)
database = peewee.SqliteDatabase("clients.db")
_client_choice = []
_club_card_to_save = defaultdict(dict)
_users_buy_card = {}
_names_of_trainings_set = set()
_trainings_by_date = {}
_trainings_to_records = defaultdict(dict)
_manager_id = 513981644
_user_name_to_manager = {}


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


def push_messages():  # сообщение об окончании абонемента за 3 дня до конца
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    contact_the_manager = types.KeyboardButton('Связаться с менеджером')
    markup.add(contact_the_manager)
    for clients in ClubCards.select():
        today = datetime.datetime.now()
        date_of_end_three_days = datetime.datetime.strptime(clients.date_of_the_end, '%d.%m.%Y')
        if today.day == (date_of_end_three_days - (timedelta(3))).day:
            mess = f'{clients.name} {messages.PUSH_MESSAGE_END_OF_THE_CARD} {clients.date_of_the_end}!'
            bot.send_message(chat_id=clients.user_id, text=mess, disable_notification=True, reply_markup=markup)


def push_messages_workout_reminder():  # сообщение о записи на тренировку на завтра
    df_record = pd.read_excel('records.xlsx')
    df_tr = pd.read_excel('trainings.xlsx')
    tomorrow = (datetime.date.today() + (timedelta(1))).strftime('%d.%m.%Y')
    mess_0 = 'Добрый день!\n\nХотим напомнить, что завтра Вы записаны на тренировку:'
    for i in df_record.itertuples():
        if i.date == tomorrow:
            if mess_0:
                bot.send_message(chat_id=i.user_id, text=mess_0)
                mess_0 = None
            for y in df_tr.itertuples():
                if i.id_workout == y.id_workout:
                    mess = f'Тренировка - {y.title}\nВремя - {i.time}'
                    bot.send_message(chat_id=i.user_id, text=mess)
                    break


def date_of_training(re_day):  # просчет всех выбранных дат до конца месяца
    obj = calendar.Calendar()
    today = datetime.date.today()
    dates = []
    days = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3, 'Пятница': 4, 'Суббота': 5, 'Воскресенье': 6}
    for i in obj.itermonthdates(today.year, today.month):
        if today <= i and i.month == today.month:
            day = calendar.weekday(i.year, i.month, i.day)
            if day == days[re_day.group()]:
                dates.append(i)
    return dates


@bot.message_handler(commands=['start'])  # старт работы бота
def start(message):
    _user_name = user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = user_cards_in_db(user_id=message.from_user.id)
    mess = f'{_user_name}, {messages.GREETING_MESSAGE}'
    sticker = open('images/hello_sticker.webp', 'rb')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)  # создаем кнопки главного меню
    main_menu = ['Общая информация', 'Клубные карты', 'Записаться на тренировку', 'Мои записи',
                 'Время работы клуба', 'Связаться с менеджером', '']
    for i in main_menu:
        markup.add(i)
    bot.send_sticker(message.chat.id, sticker)
    bot.send_message(message.chat.id, mess, reply_markup=markup)


@bot.message_handler(content_types=['text'])  # обработка текстовых запросов от пользователя
def get_user_text(message):
    global _users_buy_card, _names_of_trainings_set, _user_name_to_manager
    user_id_to_dict = str(message.from_user.id)
    day_of_week_pattern = r'Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье'
    date_pattern = r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}'
    time_pattern = r'[0-9]{2}:[0-9]{2}'
    day_for_training = re.search(day_of_week_pattern, message.text)
    date_for_training = re.search(date_pattern, message.text)
    time_for_training = re.search(time_pattern, message.text)
    _user_name = user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = user_cards_in_db(user_id=message.from_user.id)
    df = pd.read_excel('base_cards.xlsx')  # чтение абонементов из Excel заполняются менеджером
    df_tr = pd.read_excel('trainings.xlsx')  # чтение тренировок из Excel заполняются менеджером
    df_record = pd.read_excel('records.xlsx')  # чтение записей на тренировки из Excel
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if _user_name_to_manager:
        phone_number_pattern = r'0[0-9]{9}'
        phone_number = re.search(phone_number_pattern, message.text)
        if phone_number:
            restart = '/start'
            markup.add(restart)
            mess = messages.PHONE_NUMBER_MESSAGE
            mess_to_manager = f"Клиент - {phone_number.group()}!\nЗапрос на личную переписку!"
            bot.send_message(message.chat.id, mess, reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
            bot.send_message(chat_id=_manager_id, text=mess_to_manager, parse_mode='html')
            del _user_name_to_manager[message.chat.id]
        else:
            mess = messages.INCORRECT_PHONE_NUMBER_MESSAGE
            bot.send_message(message.chat.id, mess, parse_mode='html')

    elif message.text in ['Общая информация', 'Время работы клуба']:
        restart = '/start'
        markup.add(restart)
        bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')

    elif message.text == 'Связаться с менеджером':

        if not message.from_user.username:
            restart = '/start'
            markup.add(restart)
            _user_name_to_manager[message.chat.id] = message.from_user.username
            mess = messages.USER_PHONE_NUMBER_MESSAGE
            bot.send_message(message.chat.id, text=mess, parse_mode='html')
            bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
        else:
            restart = '/start'
            markup.add(restart)
            mess = f'Клиент - @{message.from_user.username}!\nЗапрос на личную переписку!'
            bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
            bot.send_message(chat_id=_manager_id, text=mess, parse_mode='html')

    elif message.text == 'Мои записи':
        restart = '/start'
        markup.add(restart)
        record = False
        for i in df_record.itertuples():
            today = datetime.datetime.now()
            date_of_records = datetime.datetime.strptime(i.date, '%d.%m.%Y')
            if date_of_records >= today:
                if i.user_id == message.chat.id:
                    for x in df_tr.itertuples():
                        if x.id_workout == i.id_workout:
                            mess = f'Тренировка - {x.title}\nДень - {i.date}\nВремя - {i.time}'
                            bot.send_message(message.chat.id, mess)
                            record = True
                            break
        if not record:
            bot.send_message(message.chat.id, "У вас нет записей!")
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, reply_markup=markup)

    elif message.text == 'Записаться на тренировку':  # Меню с перечнем доступных тренировок
        mess = messages.CHOICE_TRAININGS_MESSAGE
        _names_of_trainings_set = set((i.title) for i in df_tr.itertuples())
        for y in _names_of_trainings_set:
            trainings = types.KeyboardButton(y)
            markup.add(trainings)
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif message.text in _names_of_trainings_set:  # Меню с днем недели + время тренировки
        _trainings_to_records[user_id_to_dict]['training'] = message.text
        for i in df_tr.itertuples():
            if message.text == i.title:
                _trainings_to_records[user_id_to_dict]['id_training'] = i.id_workout
                training = types.KeyboardButton(f'{i.day_of_the_week} '
                                                f'в {i.time.strftime("%H:%M")}')
                markup.add(training)
        mess = messages.CHOICE_TRAININGS_MESSAGE_2
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif day_for_training:  # Проверка доступных тренировок и свободных мест записи. Нужно переписать по функциям!!!!
        _trainings_to_records[user_id_to_dict]['day'] = day_for_training.group()
        _trainings_to_records[user_id_to_dict]['time'] = time_for_training.group()
        if not date_of_training(re_day=day_for_training):
            mess = messages.RECORD_FULL_MESSAGE
            for y in _names_of_trainings_set:
                trainings = types.KeyboardButton(y)
                markup.add(trainings)
            bot.send_message(message.chat.id, mess, reply_markup=markup)
        else:
            max_people = 0
            signed_up_people = 0
            record = False
            mess = messages.CHOICE_TRAININGS_MESSAGE_3
            for x in df_tr.itertuples():
                if x.id_workout == _trainings_to_records[user_id_to_dict]['id_training']:
                    max_people = x.max_people
            for i in date_of_training(re_day=day_for_training):
                for y in df_record.itertuples():
                    if y.user_id == message.chat.id and \
                            y.id_workout == _trainings_to_records[user_id_to_dict]['id_training'] and \
                            y.time == _trainings_to_records[user_id_to_dict]['time'] and \
                            y.date == i.strftime("%d.%m.%Y"):
                        signed_up_people += 1
                        record = True
                    if y.user_id == message.chat.id and \
                            y.time == _trainings_to_records[user_id_to_dict]['time'] and \
                            y.date == i.strftime("%d.%m.%Y"):
                        record = True
            if record:
                restart = '/start'
                mess = messages.YOU_ARE_ALREADY_REGISTERED_MESSAGE
                for y in _names_of_trainings_set:
                    trainings = types.KeyboardButton(y)
                    markup.add(trainings)
                markup.add(restart)
                bot.send_message(message.chat.id, mess, reply_markup=markup)
                bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
            elif (max_people - signed_up_people) == 0:
                mess = messages.NO_FREE_SESSIONS_MESSAGE
                for y in _names_of_trainings_set:
                    trainings = types.KeyboardButton(y)
                    markup.add(trainings)
                bot.send_message(message.chat.id, mess, reply_markup=markup)
            else:
                training_date = types.KeyboardButton(
                    f'{i.strftime("%d.%m.%Y")}(осталось мест: {max_people - signed_up_people})')
                markup.add(training_date)
                bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif date_for_training:
        date_to_dict = re.search(date_pattern, message.text)
        restart = '/start'
        sticker = open('images/training_sticker.webp', 'rb')
        markup.add(restart)
        _trainings_to_records[user_id_to_dict]['date'] = date_to_dict.group()
        data_record = ({'user_id': message.chat.id,
                        'id_workout': _trainings_to_records[user_id_to_dict]['id_training'],  # !!!!!Падает Бот!!!!!!
                        'date': _trainings_to_records[user_id_to_dict]["date"],
                        'time': _trainings_to_records[user_id_to_dict]["time"]
                        })
        file_records = pd.read_excel('records.xlsx')
        df = pd.DataFrame(file_records)
        df_new = df.append(data_record, ignore_index=True)
        with ExcelWriter('records.xlsx', mode='a' if os.path.exists('records.xlsx') else 'w',
                         if_sheet_exists='replace') as writer:
            df_new.to_excel(writer, index=False)
        mess = f'Вы записались на тренировку - {_trainings_to_records[user_id_to_dict]["training"]}!\n' \
               f'Ждем вас на тренировку {_trainings_to_records[user_id_to_dict]["date"]} в ' \
               f'{_trainings_to_records[user_id_to_dict]["time"]}'
        bot.send_sticker(message.chat.id, sticker)
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, reply_markup=markup)
        print(_trainings_to_records)
    elif message.text == 'Клубные карты':  # меню клубных карт для покупки клиента
        _client_choice.clear()
        mess = f"{_user_club_cards}\n\n{messages.CHOICE_CLUB_CARD_MESSAGE}"
        for i in df.itertuples():
            abon_from_manadger = types.KeyboardButton(f"{i.title}: Срок-{i.validity} дней, цена-{i.price} грн")
            markup.add(abon_from_manadger)
            _client_choice.append(f"{i.title}: Срок-{i.validity} дней, цена-{i.price} грн")
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif message.text in _client_choice:  # подтверждение о покупке абонемента
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
    schedule.every().day.at("12:00").do(push_messages_workout_reminder)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    chat_bot = threading.Thread(target=run_bot)
    push_mess = threading.Thread(target=run_push_message)
    chat_bot.start()
    push_mess.start()
