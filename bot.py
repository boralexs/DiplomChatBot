from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import config
import utils
import time

dir_user_kash = 'user_kash/'
dir_check_dialog = 'check_dialog/'
bot = TeleBot(config.token)


# ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ ГРУППОВОЙ ЧАТ

@bot.message_handler(commands=['startgroup'])  # Функция реагирует только на команду /startgroup
# Начало дилога в групповом чате. Создает сообщение со ссылкой, для начала общения с ботом.
def send_welcome(message):
    keyboard = InlineKeyboardMarkup(row_width=1)  # Клавиатура с одной кнопкой
    yes = InlineKeyboardButton(text='Конечно', url='https://t.me/CourseworkBot?start=start')
    keyboard.add(yes)
    bot.send_message(message.chat.id, 'Здравствуйте я бот для сбора мнений по фильмам.\nЕсли хотите со мной '
                                      'пообщаться, перейдите по ссылке.\n (Если нет, просто игнорируйте это сообщение '
                                      'и можете покинуть группу)', reply_markup=keyboard)
    bot.delete_message(message.chat.id, message.message_id)  # удаляем ненужное страрт, чтобы не захламлять


# ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ ЛИЧНЫЕ ЧАТЫ

@bot.message_handler(commands=['start'])  # Функция реагирует только на команду /start
# Начало диалога с пользователем, спрашиваем свободен ли он
def send_start(message):
    name_user = message.from_user.first_name + " " + message.from_user.last_name
    # Создаем, если не существовала, базу BDUser
    with utils.BD() as db:
        db.add_user(message.from_user.id, name_user)  # Добавляем пользователя
    file_user = open(dir_check_dialog + str(message.from_user.id) + '.txt', "w")
    file_user.write('1')
    file_user.close()
    keyboard = InlineKeyboardMarkup(row_width=2)
    question = 'Приветствую ' + name_user + '. Я бот, который собирает мнения о текущих фильмах. ' \
                                            'Удобно сейчас пообщаться?'
    yes = InlineKeyboardButton(text='Конечно', callback_data='yes0')
    no = InlineKeyboardButton(text='В другой раз', callback_data='no0')
    keyboard.add(yes, no)
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
    bot.delete_message(message.chat.id, message.message_id)


def send_start_repeat(chat_id):
    time.sleep(3600)
    keyboard = InlineKeyboardMarkup(row_width=2)
    question = 'Приветствую еще раз! Удобно сейчас пообщаться?'
    yes = InlineKeyboardButton(text='Конечно', callback_data='yes0')
    no = InlineKeyboardButton(text='В другой раз', callback_data='no0')
    keyboard.add(yes, no)
    bot.send_message(chat_id, text=question, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'yes0' or call.data == 'no0')
def start_agreement_yes(call: CallbackQuery):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data == 'no0':
        new_message = bot.send_message(call.message.chat.id, 'Хорошо напишу позже')
        time.sleep(5)
        bot.delete_message(new_message.chat.id, new_message.message_id)
        send_start_repeat(call.message.chat.id)
    else:
        new = utils.BD('BD.sqlite')
        arr = new.check_notvalid_comm(call.from_user.id)
        if len(arr) != 0:
            film_name = new.conn.execute('SELECT film_name FROM Films WHERE film_id = (?)', (arr[0],)).fetchall()
            com = new.conn.execute('SELECT rating1, rating2, rating3, rating4, rating5, comm_text '
                                   'FROM Comments '
                                   'WHERE film_id = (?) and user_id = (?)', (arr[0], arr[1],)).fetchall()
            rate = str(int((com[0][0] + com[0][1] + com[0][2] + com[0][3] + com[0][4]) / 10))
            text = 'Можешь пожалуйста помочь мне понять, является ли коментарий к фильму "' + film_name[0][0] + \
                   '" состоятельным, относительно оставленой оценки?\n' + \
                   'Оценка (где 0-фильм ужасен, 10-фильм прекрасен): \n' + rate + \
                   '\nКомментарий: \n"' + com[0][5] + '".'
            keyboard = InlineKeyboardMarkup(row_width=3)
            yes = InlineKeyboardButton(text='Да', callback_data='yes1')
            no = InlineKeyboardButton(text='Нет', callback_data='no1')
            diff = InlineKeyboardButton(text='Затрудняюсь ответить', callback_data='diff')
            keyboard.add(yes, no, diff)
            bot.send_message(call.message.chat.id, text=text, reply_markup=keyboard)
            file_user = open(dir_user_kash + str(call.from_user.id) + '.txt', "w")
            file_user.write(film_name[0][0])
            file_user.close()
        else:
            keyboard = InlineKeyboardMarkup(row_width=2)
            question = 'Понял. Ходил(а) недавно в кино?'
            yes = InlineKeyboardButton(text='Да', callback_data='y2')
            no = InlineKeyboardButton(text='Нет', callback_data='n2')
            keyboard.add(yes, no)
            bot.send_message(call.message.chat.id, text=question, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'yes1' or call.data == 'no1' or call.data == 'diff')
def send_what_film(call: CallbackQuery):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    new = utils.BD('BD.sqlite')
    if call.data == 'yes':
        file_user = open(dir_user_kash + str(call.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        new.resize_second_check(new.film_name_to_id(film_name), call.from_user.id, 1)
    elif call.data == 'no':
        file_user = open(dir_user_kash + str(call.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        new.resize_second_check(new.film_name_to_id(film_name), call.from_user.id, 0)
    keyboard = InlineKeyboardMarkup(row_width=2)
    question = 'Спасибо, я тебя понял. Ходил(а) недавно в кино?'
    yes = InlineKeyboardButton(text='Да', callback_data='y2')
    no = InlineKeyboardButton(text='Нет', callback_data='n2')
    keyboard.add(yes, no)
    bot.send_message(call.message.chat.id, text=question, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "y2")
def what_film(call: CallbackQuery):
    new_message = bot.send_message(call.message.chat.id, 'Как называется фильм?')
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(new_message, get_film)


def get_film(message):
    if message.text[0] == '/':
        mes = bot.send_message(message.from_user.id, text='Извините, но фильм не может начинаться с "/". Повторите ввод.')
        bot.register_next_step_handler(message, get_film)
        return
    new = utils.BD('BD.sqlite')
    if new.check_film(new.film_name_to_id(message.text)):
        question = 'Я такой знаю. Как он тебе? Оставь оценку.\nОцени сюжет:'
        new.add_seen_user(new.film_name_to_id(message.text), message.from_user.id)
    else:
        question = 'Я такой не знаю. И как он тебе? Оставь оценку.\nОцени сюжет:'
        new.add_film(message.text, message.from_user.id)
    new.add_comment(new.film_name_to_id(message.text), message.from_user.id)
    keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)  # наша клавиатура
    keyboard.row("1", "2", "3", "4", "5")
    keyboard.row("6", "7", "8", "9", "10")
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
    file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "w")
    file_user.write(str(message.text))
    file_user.close()
    bot.register_next_step_handler(message, add_rating1)


def add_rating1(message):
    s = message.text
    if s.isdigit() and 0 < int(s) < 11:
        new = utils.BD('BD.sqlite')
        file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        print(film_name)
        new.set_comment(new.film_name_to_id(film_name), message.from_user.id, 'rating1', int(message.text))
        question = 'Оцени монтаж(Как снято? Ляпы?):'
        keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)  # наша клавиатура
        keyboard.row("1", "2", "3", "4", "5")
        keyboard.row("6", "7", "8", "9", "10")
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
        bot.register_next_step_handler(message, add_rating2)
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод, пожалуйста введите цифру от 1 до 10')
        bot.register_next_step_handler(message, add_rating1)


def add_rating2(message):
    s = message.text
    if s.isdigit() and 0 < int(s) < 11:
        new = utils.BD('BD.sqlite')
        file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        new.set_comment(new.film_name_to_id(film_name), message.from_user.id, 'rating2', int(message.text))
        question = 'Оцени диалоги:'
        keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)  # наша клавиатура
        keyboard.row("1", "2", "3", "4", "5")
        keyboard.row("6", "7", "8", "9", "10")
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
        bot.register_next_step_handler(message, add_rating3)
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод, пожалуйста введите цифру от 1 до 10')
        bot.register_next_step_handler(message, add_rating1)


def add_rating3(message):
    s = message.text
    if s.isdigit() and 0 < int(s) < 11:
        new = utils.BD('BD.sqlite')
        file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        new.set_comment(new.film_name_to_id(film_name), message.from_user.id, 'rating3', int(message.text))
        question = 'Оцени персонажей:'
        keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)  # наша клавиатура
        keyboard.row("1", "2", "3", "4", "5")
        keyboard.row("6", "7", "8", "9", "10")
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
        bot.register_next_step_handler(message, add_rating4)
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод, пожалуйста введите цифру от 1 до 10')
        bot.register_next_step_handler(message, add_rating1)


def add_rating4(message):
    s = message.text
    if s.isdigit() and 0 < int(s) < 11:
        new = utils.BD('BD.sqlite')
        file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        new.set_comment(new.film_name_to_id(film_name), message.from_user.id, 'rating4', int(message.text))
        question = 'Оцени звук:'
        keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)  # наша клавиатура
        keyboard.row("1", "2", "3", "4", "5")
        keyboard.row("6", "7", "8", "9", "10")
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
        bot.register_next_step_handler(message, add_rating5)
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод, пожалуйста введите цифру от 1 до 10')
        bot.register_next_step_handler(message, add_rating1)


def add_rating5(message):
    s = message.text
    if s.isdigit() and 0 < int(s) < 11:
        new = utils.BD('BD.sqlite')
        file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
        film_name = file_user.read()
        file_user.close()
        new.set_comment(new.film_name_to_id(film_name), message.from_user.id, 'rating5', int(message.text))
        bot.send_message(message.from_user.id, 'Полжалуйста оставь небольшой комментарий:')
        bot.register_next_step_handler(message, add_comment)
    else:
        bot.send_message(message.from_user.id, 'Неверный ввод, пожалуйста введите цифру от 1 до 10')
        bot.register_next_step_handler(message, add_rating1)


def add_comment(message):
    if message.text[0] == '/':
        mes = bot.send_message(message.from_user.id, text='Извините, но комментарий не может начинаться с "/".')
        time.sleep(5)
        bot.delete_message(mes.chat.id, mes.message_id)
        bot.register_next_step_handler(message, get_film)
        return
    new = utils.BD('BD.sqlite')
    file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
    film_name = file_user.read()
    file_user.close()
    new.set_comment(new.film_name_to_id(film_name), message.from_user.id, 'comm_text', message.text)
    bot.send_message(message.from_user.id, 'Большое спасибо за оставленный отзыв!)')
    new.validation_comment(new.film_name_to_id(film_name), message.from_user.id)
    file_user = open(dir_user_kash + str(message.from_user.id) + '.txt', "r")
    check_dialog = file_user.read()
    file_user.close()
    if check_dialog == '1':
        send_start_repeat(message.chat.id)
    else:
        file_user = open(dir_check_dialog + str(message.from_user.id) + '.txt', "w")
        file_user.write('1')
        file_user.close()
    utils.update_film_rating()


# Продолжение после start_agreement_yes, где 'Ходил(а) недавно в кино?' после ответа: Нет
@bot.callback_query_handler(func=lambda call: call.data == "n2")
def know_this_films(call: CallbackQuery):
    bot.delete_message(call.message.chat.id,call.message.message_id)
    new = utils.BD('BD.sqlite')
    arr = new.films_not_watch_user(call.from_user.id)
    print(arr)
    if len(arr) < 3:
        m = bot.send_message(call.message.chat.id, 'Понял.\nСпрошу в другой раз')
        time.sleep(5)
        bot.delete_message(call.message.chat.id, m.message_id)
        send_start_repeat(call.message.chat.id)
    else:
        arr2 = []
        question = 'Может знаешь какой то из этих фильмов?\nМожешь выбрать один и оценить?'
        keyboard = InlineKeyboardMarkup(row_width=4)
        for i in arr[0:3]:
            res = new.conn.execute('SELECT film_name FROM Films WHERE film_id = (?)', (i,)).fetchall()
            arr2.append(res[0][0])
        f1 = InlineKeyboardButton(text=arr2[0], callback_data=arr[0])
        f2 = InlineKeyboardButton(text=arr2[1], callback_data=arr[1])
        f3 = InlineKeyboardButton(text=arr2[2], callback_data=arr[2])
        ex = InlineKeyboardButton(text='Не знаю/Не могу/Не сейчас', callback_data='ex')
        keyboard.row(f1)
        keyboard.row(f2)
        keyboard.row(f3)
        keyboard.row(ex)
        bot.send_message(call.message.chat.id, text=question, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def know_film(call: CallbackQuery):
    new = utils.BD('BD.sqlite')
    new.add_comment((call.data,), call.from_user.id)
    new.add_seen_user((call.data,), call.from_user.id)
    res = new.conn.execute('SELECT film_name FROM Films WHERE film_id = (?)', (call.data,)).fetchall()
    print(res)
    question = res[0][0] + '\nОцени сюжет:'
    keyboard = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)  # наша клавиатура
    keyboard.row("1", "2", "3", "4", "5")
    keyboard.row("6", "7", "8", "9", "10")
    message = bot.send_message(call.from_user.id, text=question, reply_markup=keyboard)
    file_user = open(dir_user_kash + str(call.from_user.id) + '.txt', "w")
    file_user.write(res[0][0])
    file_user.close()
    bot.register_next_step_handler(message, add_rating1)


@bot.callback_query_handler(func=lambda call: call.data == 'ex')
def don_t_know_film(call: CallbackQuery):
    bot.send_message(call.message.chat.id, 'Понял.\nСпрошу в другой раз')
    send_start_repeat(call.message.chat.id)


@bot.message_handler(commands=['film'])
def send_menu(message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    question = 'Вы хотите пройти опрос или узнать рейтинг фильма?'
    yes = InlineKeyboardButton(text='Опрос', callback_data='opr')
    no = InlineKeyboardButton(text='Рейтинг', callback_data='rat')
    keyboard.add(yes, no)
    bot.send_message(message.chat.id, text=question, reply_markup=keyboard)
    bot.delete_message(message.chat.id, message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'opr' or call.data == 'rat')
def opr_or_rat(call: CallbackQuery):
    if call.data == 'opr':
        file_user = open(dir_check_dialog + str(call.from_user.id) + '.txt', "w")
        file_user.write('0')
        file_user.close()
        what_film(call)
    elif call.data == 'rat':
        new_message = bot.send_message(call.message.chat.id, 'Как называется фильм, который вас интересует?')
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(new_message, rat)


def rat(message):
    utils.update_film_rating()
    new = utils.BD('BD.sqlite')
    film_id = new.film_name_to_id(message.text)
    if new.check_film(film_id):
        x = new.conn.execute('SELECT rating1 FROM Films WHERE film_id = (?)', film_id).fetchall()
        if x[0] != 0:
            text = 'Я такой знаю. Вот что мне известно:'
            res = new.get_film(film_id)
            text = text + '\nОценка сюжета: ' + str(res[0][3]) + \
                   '\nОценка монтажа: ' + str(res[0][4]) + \
                   '\nОценка диалогов: ' + str(res[0][5]) + \
                   '\nОценка персонажей: ' + str(res[0][6]) + \
                   '\nОценка озвучивания: ' + str(res[0][7]) + \
                   '\nКОММЕНТАРИИ:\n'
            res = new.get_comment(film_id)
            for i in range(1, len(res) + 1):
                text = text + str(i) + ': "' + str(res[0][3]) + '"; \n'
        else:
            text = 'Я такой знаю. Но информации по нему нет. Его еще не оценивали.'
    else:
        text = 'Извиняюсь, я такой не знаю.'
    bot.send_message(message.chat.id, text)


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print("Ошибка соединения. Повтор через 5 секунд")
            time.sleep(5)

