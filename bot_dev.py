import telebot
from text_responses import *
from telebot import types
import peewee
import pandas as pd
import datetime
from datetime import timedelta

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read()

bot = telebot.TeleBot(TOKEN)
database = peewee.SqliteDatabase("clients.db")
_client_choice = []
_club_card_to_save = {}
_users_buy_card = {}


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
    _user_club_cards = f'У вас нет действующих абонементов!'
    for clients in ClubCards.select():
        if user_id == clients.user_id:
            _user_club_cards = f'У Вас есть действующий абонемент - {clients.title}\n' \
                               f'Дата покупки: {clients.date_of_buy}\n' \
                               f'Срок действия до: {clients.date_of_the_end}\n' \
                               f'Стоимость: {clients.price} грн.'
    return _user_club_cards


@bot.message_handler(commands=['start'])  # старт работы бота
def start(message):
    _user_name = user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = user_cards_in_db(user_id=message.from_user.id)
    mess = f'Привет, {_user_name}! \n' \
           f'Это фитнес клуб "X-GUM"!\n\n' \
           f'Мы рады что ты выбрал именно нас для улучшения своей физической формы!\n\n' \
           f'Мы готовы ответить на все твои вопросы, выбери раздел:'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем главное меню
    general_information = types.KeyboardButton('Общая информация')
    clubs_card = types.KeyboardButton('Клубные карты')
    sign_up_for_a_workout = types.KeyboardButton('Записаться на тренировку')
    working_hours = types.KeyboardButton('Время работы клуба')
    contact_the_manager = types.KeyboardButton('Связаться с менеджером')
    markup.add(general_information, clubs_card, sign_up_for_a_workout, working_hours, contact_the_manager)
    bot.send_message(message.chat.id, mess, reply_markup=markup)


@bot.message_handler(content_types=['text'])  # обработка текстовых запросов от пользователя
def get_user_text(message):
    global _users_buy_card
    _user_name = user_name(first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    _user_club_cards = user_cards_in_db(user_id=message.from_user.id)
    df = pd.read_excel('base_cards.xlsx')  # чтение абонементов из Excel заполняются менеджером
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if message.text in ['Общая информация', 'Записаться на тренировку', 'Время работы клуба',
                        'Связаться с менеджером']:
        restart = '/start'
        markup.add(restart)
        mess = 'Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, text_responses[message.text], reply_markup=markup)
        bot.send_message(message.chat.id, mess, parse_mode='html')
    elif message.text == 'Клубные карты':  # меню клубных карт для покупки клиента
        _client_choice.clear()
        mess = f"{_user_club_cards}\n\nВыберите подходящий вам абонемент из ниже перечисленных:"
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
        mess = f'{_user_name}, вы подтверждаете покупку? ' \
               f'Так как ваш действующий абонемент аннулируется!\n' \
               f'Если вы подтверждаете нажмите - "Купить абонемент"\n' \
               f'Для перехода в главное меню нажмите кнопку start!\n\n' \
               f'Через главное меню, вы можете связаться с менеджером ' \
               f'для уточнения деталей по вашему действующему абонементу!'
        if _user_club_cards == f'У вас нет действующих абонементов!':
            mess = f'{_user_name}, вы подтверждаете покупку?\n' \
                   f'Если ДА нажмите - "Купить абонемент"\n' \
                   f'Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)

    elif message.text == 'Купить абонемент':
        restart = '/start'
        markup.add(restart)
        for clients in ClubCards.select():  # удаление действующих абонементов из базы
            if _user_name == clients.name:
                clients.delete_instance()
        for i in df.itertuples():
            if i.title in _users_buy_card[message.from_user.id]:  # создание данных для записи в базу
                date = datetime.datetime.now()
                date_end = date + (timedelta(i.validity))
                _club_card_to_save['user_id'] = f'{message.from_user.id}'
                _club_card_to_save['name'] = f'{_user_name}'
                _club_card_to_save['title'] = i.title
                _club_card_to_save['validity'] = i.validity
                _club_card_to_save['price'] = i.price
                _club_card_to_save['date_of_buy'] = date.strftime("%d.%m.%Y")
                _club_card_to_save['date_of_the_end'] = date_end.strftime("%d.%m.%Y")
        mess = f'{_user_name}, спасибо за ваш выбор!\n' \
               f'Ваш абонемент - {_club_card_to_save["title"]}\n' \
               f'Стоимость - {_club_card_to_save["price"]}\n' \
               f'Дата покупки - {_club_card_to_save["date_of_buy"]}\n' \
               f'Действует до - {_club_card_to_save["date_of_the_end"]}\n\n' \
               f'Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        client_in_db = ClubCards.insert_many(_club_card_to_save).execute()  # запись купленного абонемента в базу
        del _users_buy_card[message.from_user.id]
        for clients in ClubCards.select():  # чтение данных из базы
            print(f'ID: {clients.user_id} | Имя: {clients.name} | '
                  f'Абонемент: {clients.title} | Срок: {clients.validity} | '
                  f'Стоимость:{clients.price} | Дата покупки: {clients.date_of_buy} | '
                  f'Действует до: {clients.date_of_the_end}')
    else:
        restart = '/start'
        markup.add(restart)
        mess = 'Выбор можно делать только по перечисленным вариантам. Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)


bot.polling(none_stop=True)
