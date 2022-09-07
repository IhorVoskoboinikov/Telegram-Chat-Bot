# -*- coding: utf-8 -*-

def get_user_cards_in_db_message(title, date_of_buy, date_of_the_end, price):
    user_club_cards = f'У Вас есть действующий абонемент - {title}\n' \
                      f'Дата покупки: {date_of_buy}\n' \
                      f'Срок действия до: {date_of_the_end}\n' \
                      f'Стоимость: {price} грн.'
    return user_club_cards


def get_a_training_session_message(title, time):
    mess = f'Тренировка - {title}\nВремя - {time.strftime("%H:%M")}'
    return mess


def request_for_personal_correspondence_message(message):
    mess = f'Клиент - @{message}!\nЗапрос на личную переписку!'
    return mess


def get_my_records_message(title, date, time):
    mess = f'Тренировка - {title}\nДень - {date}\n' \
           f'Время - {time.strftime("%H:%M")}'
    return mess


def get_datetime_button_message(day_of_the_week, time):
    button_mess = f'{day_of_the_week} в {time.strftime("%H:%M")}'
    return button_mess


def get_button_date_coach_number_people_message(date, coach, people):
    button_mess = f'{date.strftime("%d.%m.%Y")} тренер - {coach}\n(осталось мест: {people})'
    return button_mess


def get_training_session_message(training, date, time, coach):
    mess = f'Вы записались на тренировку - {training}!\n' \
           f'Ждем вас на тренировку {date} в ' \
           f'{time}\n' \
           f'Тренер - {coach}'
    return mess


def get_club_cards_message(title, validity, price):
    button_mess = f"{title}: Срок-{validity} дней, цена-{price} грн"
    return button_mess


def get_a_purchased_club_card(name, title, price, date_of_buy, date_of_the_end):
    mess = f'{name}, спасибо за Ваш выбор!\n' \
           f'Ваш абонемент - {title}\n' \
           f'Стоимость - {price} грн.\n' \
           f'Дата покупки - {date_of_buy}\n' \
           f'Действует до - {date_of_the_end}\n\n' \
           f'Для перехода в главное меню нажмите кнопку start!'
    return mess


def get_a_request_to_the_manager(phone_number):
    mess = f"Клиент - {phone_number}!\nЗапрос на личную переписку!"
    return mess


def get_confirmation_club_card_in_db_message(name):
    mess = f'{name}, {CONFIRMATION_CLUB_CARD_IN_DB_MESSAGE}'
    return mess


def get_confirmation_club_card_out_in_db_message(name):
    mess = f'{name}, {CONFIRMATION_CLUB_CARD_OUT_IN_DB_MESSAGE}'
    return mess


def get_data_from_db(user_id, name, title, validity, price, date_of_buy, date_of_the_end):
    mess = f'ID: {user_id} | Имя: {name} | Абонемент: {title} | Срок: {validity} | Стоимость:{price} | ' \
           f'Дата покупки: {date_of_buy} | Действует до: {date_of_the_end}'
    return mess


def get_coach_description_message(name):
    mess = f'{name.description}\n\n{DOES_TRAINING_MESSAGE}\n'
    return mess


def get_list_of_club_cards(user_cards):
    mess = f"{user_cards}\n\n{CHOICE_CLUB_CARD_MESSAGE}"
    return mess


GREETING_MESSAGE = f'привет! \n' \
                   f'Это фитнес клуб "X-GUM"!\n\n' \
                   f'Мы рады что Вы выбрали именно нас для улучшения своей физической формы!\n\n' \
                   f'Мы готовы ответить на все Ваши вопросы, выберите раздел:'
MAIN_MENU_MESSAGE = {
    'Общая информация': 'Фитнес-клуб «X-GUM» в Киеве находится по адресу Старонаводницкая, 13Б. '
                        'Фитнес-клуб «X-GUM» предоставляет услуги: бассейн, тренажерный зал, фитнес, детский фитнес, '
                        'спортивный массаж, йога, кардизона, пилатес, тренировки с тренером, спа.\n\n'
                        'Время работы:\n- в будни: 7:00 - 23:00\n- выходные: 9:00 - 21:00\n'
                        'С радостью ждем вас у нас в клубе!',
    'Клубные карты': 'Выберите название клубной карты:',
    'Записаться на тренировку': 'Расписание сейчас составляется, как будет готово мы вас оповестим!',
    'Связаться с менеджером': 'Менеджер свяжется с вами в ближайшее время, спасибо что выбрали именно нас!',
    'Наши тренеры': 'У нас работают лучшие тренеры Украины!\n\n'
                    'Для детальной информации выберите тренера из списка:'
}
USER_PHONE_NUMBER_MESSAGE = 'Напишите ваш номер телефона в формате\n\n0681234567\n\n' \
                            'Проверьте чтобы номер был верным и в себе хранил ТОЛЬКО цифры в количестве 10 шт'
INCORRECT_PHONE_NUMBER_MESSAGE = "Не правильно указали ваш номер телефона! " \
                                 "Проверьте чтобы номер был верным и в себе хранил ТОЛЬКО цифры в количестве 10 шт"
PHONE_NUMBER_MESSAGE = 'Ваш номер передан менеджеру, он свяжется с вами в ближайшее время!'
CHOICE_TRAININGS_MESSAGE = 'Выберите тренировку на которую хотели бы записаться из ниже перечисленных:'
CHOICE_TRAININGS_MESSAGE_2 = 'Выберите день и время тренировки из ниже перечисленных вариантов:'
CHOICE_TRAININGS_MESSAGE_3 = 'Выберите дату тренировки из ниже перечисленных вариантов:'
NO_FREE_SESSIONS_MESSAGE = 'Нет свободных мест для записи! Выберите другую тренировку или другое время!'
YOU_ARE_ALREADY_REGISTERED_MESSAGE = 'Вы уже записаны на данную тренировку или на тренировку в это же время!\n\n' \
                                     'Выберите другую тренировку или другое время!'
RECORD_FULL_MESSAGE = 'Нет доступных дат для записи в действующем месяце!\n\nВыберите другую тренировку иди дату!'
RECORD_FULL_MESSAGE_2 = 'Нет свободных мест для записи на эту тренировку!\n\nВыберите другую тренировку или время!'
USER_NO_ACCOUNT_MESSAGE = 'У вас нет действующих абонементов!'
GO_TO_MAIN_MENU_MESSAGE = 'Для перехода в главное меню нажмите кнопку start!'
CHOICE_ERROR_MESSAGE = 'Выбор можно делать только по перечисленным вариантам. ' \
                       'Для перехода в главное меню нажмите кнопку "start!"'
CHOICE_CLUB_CARD_MESSAGE = 'Выберите подходящий вам абонемент из ниже перечисленных:'
CONFIRMATION_CLUB_CARD_OUT_IN_DB_MESSAGE = 'Вы подтверждаете покупку?\n' \
                                           'Если ДА нажмите - "Купить абонемент"\n' \
                                           'Для перехода в главное меню нажмите кнопку "start!"'
CONFIRMATION_CLUB_CARD_IN_DB_MESSAGE = 'Вы подтверждаете покупку? Так как Ваш действующий абонемент аннулируется!\n' \
                                       'Если Вы подтверждаете нажмите - "Купить абонемент"\n' \
                                       'Для перехода в главное меню нажмите кнопку start!\n\n' \
                                       'Через главное меню, Вы можете связаться с менеджером для ' \
                                       'уточнения деталей по вашему действующему абонементу!'
PUSH_MESSAGE_END_OF_THE_CARD_MESSAGE = ', привет!\n' \
                                       'Напоминаем, что срок действия Вашего абонемента истекает через 3 дня!\n\n' \
                                       f'Не упусти свою скидку при непрерывном продлении в размере 10%\n\n' \
                                       f'Срок действия абонемента до '
WORKOUT_REMINDER_MESSAGE = 'Добрый день!\nХотим напомнить, что завтра Вы записаны на тренировку:'
DOES_TRAINING_MESSAGE = 'Проводит тренировки:'
YOUR_RECORDS_MESSAGE = 'Ваши записи:'
YOU_HAVE_NO_ENTRY_MESSAGE = 'У вас нет записей!'

if __name__ == '__main__':
    pass
