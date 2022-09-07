# -*- coding: utf-8 -*-
import main
import messages
from telebot import types
import pandas as pd
import datetime
from datetime import timedelta


def get_push_message_about_the_end_of_the_subscription():  # сообщение об окончании абонемента за 3 дня до конца
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    contact_the_manager = types.KeyboardButton('Связаться с менеджером')
    markup.add(contact_the_manager)
    for clients in main.ClubCards.select():
        today = datetime.datetime.now()
        date_of_end_three_days = datetime.datetime.strptime(clients.date_of_the_end, '%d.%m.%Y')
        if today.day == (date_of_end_three_days - (timedelta(3))).day:
            mess = f'{clients.name} {messages.PUSH_MESSAGE_END_OF_THE_CARD_MESSAGE} {clients.date_of_the_end}!'
            main.session.send_message(chat_id=clients.user_id, text=mess, disable_notification=True,
                                      reply_markup=markup)


def get_push_messages_workout_reminder():  # сообщение о записи на тренировку на завтра
    df_record = pd.read_excel('records.xlsx')
    df_trainings = pd.read_excel('trainings.xlsx')
    df_trainings_types = pd.read_excel('trainings_types.xlsx')
    tomorrow = (datetime.date.today() + (timedelta(1))).strftime('%d.%m.%Y')
    mess_0 = messages.WORKOUT_REMINDER_MESSAGE
    id_push_mass = set(i.user_id for i in df_record.itertuples() if i.date == tomorrow)
    for i in id_push_mass:
        main.session.bot.send_message(chat_id=i, text=mess_0)
    for i in df_record.itertuples():
        if i.date == tomorrow:
            for y in df_trainings.itertuples():
                if i.training_id == y.training_id:
                    for z in df_trainings_types.itertuples():
                        if y.training_type_id == z.training_type_id:
                            mess = messages.get_a_training_session_message(title=z.title, time=y.time)
                            main.session.bot.send_message(chat_id=i.user_id, text=mess)
                            break


if __name__ == "__main__":
    pass
