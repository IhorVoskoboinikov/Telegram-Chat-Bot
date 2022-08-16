import telebot
from text_responses import *
from telebot import types
import peewee
import pandas as pd
import datetime

with open('token.txt', 'r') as token_file:
    TOKEN = token_file.read()

bot = telebot.TeleBot(TOKEN)
database = peewee.SqliteDatabase("clients.db")
_client_choice = []
_club_card_to_save = {}
_user_name = None
_user_club_cards = None
_user_buy_card = None


class BaseTable(peewee.Model):
    class Meta:
        database = database


class ClubCards(BaseTable):
    name = peewee.CharField()
    title = peewee.CharField()
    validity = peewee.IntegerField()
    price = peewee.IntegerField()
    date = peewee.DateTimeField()


ClubCards.create_table()


@bot.message_handler(commands=['start'])  # старт работы бота
def start(message):
    global _user_name, _user_club_cards
    _user_name = f'{message.from_user.first_name} {message.from_user.last_name}'
    if not message.from_user.last_name:
        _user_name = f'{message.from_user.first_name}'
    _user_club_cards = f'У вас нет действующих абонементов!'
    for clients in ClubCards.select():
        if _user_name in clients.name:
            _user_club_cards = f'У Вас есть действующий абонемент - {clients.title}\nСрок: {clients.validity}' \
                               f' от даты покупки\nДата покупки: {clients.date}'
    mess = f'Привет, {_user_name}! \n' \
           f'Это фитнес клуб "Tsarsky City Resort "!\n\n' \
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
    global _user_buy_card
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
        _user_buy_card = message.text
        restart = '/start'
        i_agree = 'Купить абонемент'
        markup.add(restart, i_agree)
        mess = f'{_user_name}, вы подтверждаете покупку? Так как ваш действующий абонемент аннулируется!\n' \
               f'Если вы подтверждаете нажмине - "Купить абонемент"\n' \
               f'Для перехода в главное меню нажмите кнопку start!\n\n' \
               f'Через главное меню, вы можете связаться с менеджером ' \
               f'для уточнения деталей по вашему действующему абонементу!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)

    elif message.text == 'Купить абонемент':
        restart = '/start'
        markup.add(restart)
        for clients in ClubCards.select():  # удаление действующих абонементов из базы
            if _user_name == clients.name:
                clients.delete_instance()
        for i in df.itertuples():
            if i.title in _user_buy_card:  # создание данных для записи в базу
                _club_card_to_save['name'] = f'{_user_name}'
                _club_card_to_save['title'] = i.title
                _club_card_to_save['validity'] = i.validity
                _club_card_to_save['price'] = i.price
                date = datetime.datetime.now()
                _club_card_to_save['date'] = date.strftime("%d.%m.%Y")
        mess = f'{_user_name}, спасибо за ваш выбор!\n' \
               f'Ваш абонемент - {_club_card_to_save["title"]}\n' \
               f'Срок действия - {_club_card_to_save["validity"]}\n' \
               f'Дата покупки - {_club_card_to_save["date"]}\n\n' \
               f'Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)
        client_in_db = ClubCards.insert_many(_club_card_to_save).execute()  # запись купленного абонемента в базу
        for clients in ClubCards.select():  # чтение данных из базы
            print(f'Имя: {clients.name} | Абонемент: {clients.title} | Срок: {clients.validity} | '
                  f'Стоимость:{clients.price} | Дата покупки: {clients.date}')
    else:
        restart = '/start'
        markup.add(restart)
        mess = 'Выбор можно делать только по перечисленным вариантам. Для перехода в главное меню нажмите кнопку start!'
        bot.send_message(message.chat.id, mess, reply_markup=markup)


bot.polling(none_stop=True)
