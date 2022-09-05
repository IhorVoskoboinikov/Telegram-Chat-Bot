# -*- coding: utf-8 -*-
import threading
import time
import schedule
import telebot
import messages
import pushes
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

with open('manager_id.txt', 'r') as manager_id_file:
    _manager_id = int(manager_id_file.read())

bot = telebot.TeleBot(TOKEN)
database = peewee.SqliteDatabase("clients.db")
_client_choice = defaultdict(list)
_club_card_to_save = defaultdict(dict)
_users_buy_card = {}
_names_of_trainings_set = set()
_trainings_by_date = {}
_trainings_to_records = defaultdict(dict)
_user_name_to_manager = {}
_name_of_coaches_set = set()


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


def get_user_name(first_name, last_name):  # функция проверки и присвоения имени пользователя
    user_name = f'{first_name} {last_name}'
    if not last_name:
        user_name = f'{first_name}'
    return user_name


def get_user_cards_in_db(user_id):  # функция проверки наличия абонементов в базе
    _user_club_cards = messages.USER_NO_ACCOUNT_MESSAGE
    for clients in ClubCards.select():
        if user_id == clients.user_id:
            _user_club_cards = messages.get_user_cards_in_db_message(title=clients.title,
                                                                     date_of_buy=clients.date_of_buy,
                                                                     date_of_the_end=clients.date_of_the_end,
                                                                     price=clients.price)

    return _user_club_cards


def get_all_dates_before_the_end_of_the_month(re_day):  # просчет всех выбранных дат до конца месяца
    obj = calendar.Calendar()
    today = datetime.date.today()
    dates = []
    days = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3, 'Пятница': 4, 'Суббота': 5, 'Воскресенье': 6}
    for i in obj.itermonthdates(today.year, today.month):
        if today <= i:  # and i.month == today.month: # если нужно до конца месяца нужно равенство
            day = calendar.weekday(i.year, i.month, i.day)
            if day == days[re_day.group()]:
                dates.append(i)
    return dates


@bot.message_handler(commands=['start'])  # старт работы бота
def start(message):
    _user_name = get_user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = get_user_cards_in_db(user_id=message.from_user.id)
    mess = f'{_user_name}, {messages.GREETING_MESSAGE}'
    sticker = open('images/hello_sticker.webp', 'rb')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)  # создаем кнопки главного меню
    main_menu = ['Общая информация', 'Клубные карты', 'Записаться на тренировку', 'Мои записи',
                 'Наши тренеры', 'Связаться с менеджером']
    for i in main_menu:
        markup.add(i)
    bot.send_sticker(message.chat.id, sticker)
    bot.send_message(message.chat.id, mess, reply_markup=markup)


@bot.message_handler(content_types=['text'])  # обработка текстовых запросов от пользователя
def get_user_text(message):
    global _users_buy_card, _names_of_trainings_set, _user_name_to_manager, _name_of_coaches_set
    user_id_to_dict = str(message.from_user.id)
    day_of_week_pattern = r'Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье'
    date_pattern = r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}'
    time_pattern = r'[0-9]{2}:[0-9]{2}'
    day_for_training = re.search(day_of_week_pattern, message.text)
    date_for_training = re.search(date_pattern, message.text)
    time_for_training = re.search(time_pattern, message.text)
    _user_name = get_user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = get_user_cards_in_db(user_id=message.from_user.id)
    df = pd.read_excel('base_cards.xlsx')  # чтение абонементов из Excel заполняются менеджером
    df_trainings = pd.read_excel('trainings.xlsx')  # чтение тренировок из Excel заполняются менеджером
    df_record = pd.read_excel('records.xlsx')  # чтение записей на тренировки из Excel
    df_training_types = pd.read_excel('trainings_types.xlsx')  # чтение типов тренировок из Excel
    df_coaches = pd.read_excel('coaches.xlsx')  # чтение тренеров из Excel
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if message.from_user.id in _user_name_to_manager:
        phone_number_pattern = r'0[0-9]{9}'
        phone_number = re.search(phone_number_pattern, message.text)
        if phone_number:
            restart = '/start'
            markup.add(restart)
            mess = messages.PHONE_NUMBER_MESSAGE
            mess_to_manager = messages.get_a_request_to_the_manager(phone_number=phone_number.group())
            bot.send_message(message.chat.id, mess, reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
            bot.send_message(chat_id=_manager_id, text=mess_to_manager, parse_mode='html')
            del _user_name_to_manager[message.chat.id]
        else:
            mess = messages.INCORRECT_PHONE_NUMBER_MESSAGE
            bot.send_message(message.chat.id, mess, parse_mode='html')

    elif message.text == 'Общая информация':
        restart = '/start'
        markup.add(restart)
        bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')

    elif message.text == 'Наши тренеры':
        restart = '/start'

        for i in df_coaches.itertuples():
            coach = types.KeyboardButton(i.coach_name)
            markup.add(coach)
            _name_of_coaches_set.add(i.coach_name)
        markup.add(restart)
        bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')

    elif message.text in _name_of_coaches_set:  # вынести все в отдельную функцию
        coach_name = message.text
        coach_id = None
        mess = ''
        trainings_set = set()
        for i in df_coaches.itertuples():
            if coach_name == i.coach_name:
                mess += f'{i.description}\n\n{messages.DOES_TRAINING_MESSAGE}\n'
                coach_id = i.id_coach
        for y in df_trainings.itertuples():
            if coach_id == y.id_coach:
                for z in df_training_types.itertuples():
                    if z.training_type_id == y.training_type_id:
                        trainings_set.add(z.title)
        mess += '\n'.join(trainings_set)
        bot.send_message(message.chat.id, mess, parse_mode='html')
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
            mess = messages.request_for_personal_correspondence_message(message=message.from_user.username)
            bot.send_message(message.chat.id, messages.MAIN_MENU_MESSAGE[message.text], reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
            bot.send_message(chat_id=_manager_id, text=mess, parse_mode='html')
    elif message.text == 'Мои записи':
        restart = '/start'
        markup.add(restart)
        record = False
        mess_0 = messages.YOUR_RECORDS_MESSAGE
        for i in df_record.itertuples():
            today = datetime.datetime.now()
            date_of_records = datetime.datetime.strptime(i.date, '%d.%m.%Y')
            if date_of_records >= today:
                if i.user_id == message.chat.id:
                    for y in df_trainings.itertuples():
                        if i.training_id == y.training_id:
                            for z in df_training_types.itertuples():
                                if z.training_type_id == y.training_type_id:
                                    mess = messages.get_my_records_message(title=z.title, date=i.date, time=y.time)
                                    if mess_0:
                                        bot.send_message(chat_id=message.chat.id, text=mess_0, parse_mode='html')
                                        mess_0 = None
                                    bot.send_message(message.chat.id, mess)
                                    record = True
                                    break
                            break
        if not record:
            bot.send_message(message.chat.id, "У вас нет записей!")
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, reply_markup=markup)
    elif message.text == 'Записаться на тренировку':  # Меню с перечнем доступных тренировок
        mess = messages.CHOICE_TRAININGS_MESSAGE
        _names_of_trainings_set = sorted(set((i.title) for i in df_training_types.itertuples()))
        for y in _names_of_trainings_set:
            trainings = types.KeyboardButton(y)
            markup.add(trainings)
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        restart = '/start'
        markup.add(restart)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, reply_markup=markup)
    elif message.text in _names_of_trainings_set:  # Меню с днем недели + время тренировки
        for i in df_training_types.itertuples():
            if i.title == message.text:
                _trainings_to_records[user_id_to_dict]['training_type_id'] = i.training_type_id
        _trainings_to_records[user_id_to_dict]['training'] = message.text
        for i in df_trainings.itertuples():
            if i.training_type_id == _trainings_to_records[user_id_to_dict]['training_type_id']:
                button = messages.get_datetime_button_message(day_of_the_week=i.day_of_the_week, time=i.time)
                training = types.KeyboardButton(button)
                markup.add(training)
        mess = messages.CHOICE_TRAININGS_MESSAGE_2
        bot.send_message(message.chat.id, mess, reply_markup=markup)
    elif day_for_training:  # Проверка доступных тренировок и свободных мест записи. Нужно переписать по функциям!!!!
        max_people = 0
        days_for_recording = 0
        mess = messages.CHOICE_TRAININGS_MESSAGE_3
        _trainings_to_records[user_id_to_dict]['day'] = day_for_training.group()
        _trainings_to_records[user_id_to_dict]['time'] = time_for_training.group()
        for i in df_trainings.itertuples():
            if i.training_type_id == _trainings_to_records[user_id_to_dict]['training_type_id'] and \
                    i.day_of_the_week == _trainings_to_records[user_id_to_dict]['day'] and \
                    i.time.strftime('%H:%M') == _trainings_to_records[user_id_to_dict]['time']:
                _trainings_to_records[user_id_to_dict]['training_id'] = i.training_id
        available_dates = get_all_dates_before_the_end_of_the_month(re_day=day_for_training)
        if not available_dates:  # проверяем доступные тренировки до конца Python календаря
            mess = messages.RECORD_FULL_MESSAGE
            for y in _names_of_trainings_set:
                trainings = types.KeyboardButton(y)
                markup.add(trainings)
            bot.send_message(message.chat.id, mess, reply_markup=markup)

        for x in df_trainings.itertuples():  # проверяем максимальное количество людей
            if x.training_id == _trainings_to_records[user_id_to_dict]['training_id']:
                max_people = x.max_people

        for i in available_dates:
            signed_up_people = 0
            for y in df_record.itertuples():  # проверка количества записанных людей на тренировку
                if y.date == i.strftime("%d.%m.%Y"):
                    for x in df_trainings.itertuples():
                        if x.training_id == y.training_id and \
                                x.day_of_the_week == _trainings_to_records[user_id_to_dict]['day'] and \
                                x.time.strftime('%H:%M') == _trainings_to_records[user_id_to_dict]['time']:
                            for z in df_training_types.itertuples():
                                if x.training_type_id == z.training_type_id and \
                                        z.title == _trainings_to_records[user_id_to_dict]['training']:
                                    signed_up_people += 1
                                    break
            if (max_people - signed_up_people) <= 0:
                days_for_recording += 1
                continue
            for y in df_trainings.itertuples():
                if y.training_id == _trainings_to_records[user_id_to_dict]['training_id']:
                    for x in df_coaches.itertuples():
                        if x.id_coach == y.id_coach:
                            _trainings_to_records[user_id_to_dict]['coach'] = x.coach_name
                            free_places = max_people - signed_up_people
                            button = messages.get_button_date_coach_number_people_message(date=i,
                                                                                          coach=x.coach_name,
                                                                                          people=free_places)
                            training_date = types.KeyboardButton(button)
            markup.add(training_date)
        if days_for_recording == len(available_dates):  # Проверка если во все дни полная запись и нет мест!
            restart = '/start'
            mess = messages.RECORD_FULL_MESSAGE_2
            for y in _names_of_trainings_set:
                trainings = types.KeyboardButton(y)
                markup.add(trainings)
            markup.add(restart)
            bot.send_message(message.chat.id, mess, reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
        else:
            bot.send_message(message.chat.id, mess, reply_markup=markup)

    elif date_for_training:
        record = False
        date_to_dict = re.search(date_pattern, message.text)
        restart = '/start'
        sticker = open('images/training_sticker.webp', 'rb')
        _trainings_to_records[user_id_to_dict]['date'] = date_to_dict.group()
        for i in df_record.itertuples():  # проверка записи на одну и туже тренировку
            if i.user_id == message.chat.id and \
                    i.training_id == _trainings_to_records[user_id_to_dict]['training_id'] and \
                    i.date == _trainings_to_records[user_id_to_dict]['date']:
                record = True

        for i in df_record.itertuples():  # проверка записи на разные тренировки в одинаковое время/день !!!НЕ РАБОТАЕТ!
            if i.user_id == message.chat.id and \
                    i.date == _trainings_to_records[user_id_to_dict]['date']:
                for y in df_trainings.itertuples():
                    if y.training_id == i.training_id and \
                            y.day_of_the_week == _trainings_to_records[user_id_to_dict]['day'] and \
                            y.time.strftime('%H:%M') == _trainings_to_records[user_id_to_dict]['time']:
                        record = True
                        break

        if record:
            mess = messages.YOU_ARE_ALREADY_REGISTERED_MESSAGE
            for y in _names_of_trainings_set:
                trainings = types.KeyboardButton(y)
                markup.add(trainings)
            markup.add(restart)
            bot.send_message(message.chat.id, mess, reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, parse_mode='html')
        else:
            data_record = ({'user_id': message.chat.id,
                            'training_id': _trainings_to_records[user_id_to_dict]['training_id'],  # Падает Бот!
                            'date': _trainings_to_records[user_id_to_dict]["date"]
                            })
            file_records = pd.read_excel('records.xlsx')
            df = pd.DataFrame(file_records)
            df_new = df.append(data_record, ignore_index=True)
            with ExcelWriter('records.xlsx', mode='a' if os.path.exists('records.xlsx') else 'w',
                             if_sheet_exists='replace') as writer:
                df_new.to_excel(writer, index=False)
            mess = messages.get_training_session_message(training=_trainings_to_records[user_id_to_dict]["training"],
                                                         date=_trainings_to_records[user_id_to_dict]["date"],
                                                         time=_trainings_to_records[user_id_to_dict]["time"],
                                                         coach=_trainings_to_records[user_id_to_dict]["coach"])
            markup.add(restart)
            bot.send_sticker(message.chat.id, sticker)
            bot.send_message(message.chat.id, mess, reply_markup=markup)
            bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, reply_markup=markup)
    elif message.text == 'Клубные карты':  # меню клубных карт для покупки клиента
        mess = f"{_user_club_cards}\n\n{messages.CHOICE_CLUB_CARD_MESSAGE}"
        for i in df.itertuples():
            button = messages.get_club_cards_message(title=i.title, validity=i.validity, price=i.price)
            club_cards_from_manager = types.KeyboardButton(button)
            markup.add(club_cards_from_manager)
            _client_choice[user_id_to_dict].append(button)
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        restart = '/start'
        markup.add(restart)
        bot.send_message(message.chat.id, messages.GO_TO_MAIN_MENU_MESSAGE, reply_markup=markup)
    elif message.text in _client_choice[user_id_to_dict]:  # подтверждение о покупке абонемента
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
        mess = messages.get_a_purchased_club_card(title=_club_card_to_save[user_id_to_dict]["title"],
                                                  price=_club_card_to_save[user_id_to_dict]["price"],
                                                  date_of_buy=_club_card_to_save[user_id_to_dict]["date_of_buy"],
                                                  date_of_the_end=_club_card_to_save[user_id_to_dict]["date_of_the_end"]
                                                  )
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
    schedule.every().day.at("06:00").do(pushes.get_push_message_about_the_end_of_the_subscription)
    schedule.every().day.at("12:00").do(pushes.get_push_messages_workout_reminder)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    chat_bot = threading.Thread(target=run_bot)
    push_mess = threading.Thread(target=run_push_message)
    chat_bot.start()
    push_mess.start()
