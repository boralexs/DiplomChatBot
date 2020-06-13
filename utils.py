import sqlite3
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel

valid_const = 3


class BD:
    def __init__(self, name='BD.sqlite'):
        self.name = name
        self.conn = sqlite3.connect(name)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def setup(self):
        self.conn.execute('CREATE TABLE IF NOT EXISTS User ('
                          'user_id INTEGER NOT NULL PRIMARY KEY UNIQUE,'
                          'user_name TEXT NOT NULL DEFAULT "Not name");')
        self.conn.execute('CREATE TABLE IF NOT EXISTS Films ('
                          'film_id INTEGER NOT NULL PRIMARY KEY UNIQUE,'
                          'film_name TEXT NOT NULL DEFAULT "Not name",'
                          'users_rated TEXT,'
                          'rating1 FLOAT NOT NULL DEFAULT 0,'
                          'rating2 FLOAT NOT NULL DEFAULT 0,'
                          'rating3 FLOAT NOT NULL DEFAULT 0,'
                          'rating4 FLOAT NOT NULL DEFAULT 0,'
                          'rating5 FLOAT NOT NULL DEFAULT 0);')
        self.conn.execute('CREATE TABLE IF NOT EXISTS Comments ('
                          'comm_id INTEGER NOT NULL PRIMARY KEY UNIQUE,'
                          'film_id INTEGER NOT NULL DEFAULT 0,'
                          'user_id INTEGER NOT NULL DEFAULT 0,'
                          'comm_text TEXT NOT NULL DEFAULT "Not text",'
                          'rating1 INTEGER NOT NULL DEFAULT 0,'
                          'rating2 INTEGER NOT NULL DEFAULT 0,'
                          'rating3 INTEGER NOT NULL DEFAULT 0,'
                          'rating4 INTEGER NOT NULL DEFAULT 0,'
                          'rating5 INTEGER NOT NULL DEFAULT 0,'
                          'comm_check INTEGER NOT NULL DEFAULT 0,'
                          'second_check INTEGER DEFAULT 0); ')
        self.conn.commit()

    def add_user(self, user_id, user_name):
        if not self.check_user(user_id):
            stat = 'INSERT INTO User (user_id, user_name) VALUES (?,?)'
            args = (user_id, user_name,)
            self.conn.execute(stat, args)
            self.conn.commit()

    def check_user(self, user_id):
        stat = 'SELECT user_id FROM User WHERE user_id = (?)'
        args = (user_id,)
        if len([x[0] for x in self.conn.execute(stat, args)]):
            return True
        return False

    def add_film(self, film_name, users_rated):
        if not self.check_film(self.film_name_to_id(film_name)):
            x = self.conn.execute('SELECT * FROM Films').fetchall()
            film_id = len(x) + 1
            stat = 'INSERT INTO Films (film_id, film_name, users_rated) VALUES (?,?,?)'
            args = (film_id, film_name, users_rated)
            self.conn.execute(stat, args)
            self.conn.commit()

    def check_film(self, film_id):
        if film_id == -1:
            return False
        stat = 'SELECT film_id FROM Films WHERE film_id = (?)'
        args = film_id
        if len([x[0] for x in self.conn.execute(stat, args)]):
            return True
        else:
            return False

    def add_seen_user(self, film_id, user_id):  # Добавляет к фильму пользователя, который его уже видел
        stat = f'SELECT users_rated FROM Films WHERE film_id = (?)'
        res = self.conn.execute(stat, film_id).fetchone()
        result = res[0] + ',' + str(user_id)
        stat = f'UPDATE Films SET users_rated = (?) WHERE film_id = (?)'
        self.conn.execute(stat, (result, film_id[0]))
        self.conn.commit()

    def check_user_watched_film(self, film_id, user_id):  # проверка, что пользователь смотрел фильм
        stat = f'SELECT users_rated FROM Films WHERE film_id = (?)'
        res = self.conn.execute(stat, (film_id,)).fetchone()
        if res[0]:
            result = res[0].split(',')
            if str(user_id) in result:
                return True
            else:
                return False
        return False

    def film_name_to_id(self, film_name):  # Возвращает film_id если есть, -1 если нет
        stat = 'SELECT film_id FROM Films WHERE film_name = (?)'
        args = (film_name,)
        x = self.conn.execute(stat, args).fetchall()
        if len(x):
            return x[0]
        else:
            return -1

    def films_not_watch_user(self, user_id):  # Выдает список фильмов, не отмеченных пользователем
        x = self.conn.execute('SELECT * FROM Films').fetchall()
        result = []
        for i in range(len(x)):
            if not self.check_user_watched_film(i + 1, user_id):
                result.append(i + 1)
        return result

    def get_film(self, film_id):
        if self.check_film(film_id):
            stat = 'SELECT * FROM Films WHERE film_id = (?)'
            return self.conn.execute(stat, film_id).fetchall()
        return []

    def set_film(self, film_id, item, data):  # для обновления заданного параметра по id_film
        if self.check_film(film_id):
            stat = 'UPDATE Films ' \
                   f'SET {item} = (?) ' \
                   'WHERE film_id = (?)'
            self.conn.execute(stat, (data, film_id[0]))
            self.conn.commit()

    def add_comment(self, film_id, user_id):
        x = self.conn.execute('SELECT * FROM Comments').fetchall()
        comm_id = len(x) + 1
        stat = 'INSERT INTO Comments (comm_id, film_id, user_id) VALUES (?,?,?)'
        args = (comm_id, film_id[0], user_id)
        self.conn.execute(stat, args)
        self.conn.commit()

    def set_comment(self, film_id, user_id, item, data):  # для обновления заданного параметра по film_id и user_id
        if self.check_film(film_id):
            stat = 'UPDATE Comments ' \
                   f'SET {item} = (?) ' \
                   'WHERE film_id = (?) and user_id = (?)'
            self.conn.execute(stat, (data, film_id[0], user_id))
            self.conn.commit()

    def get_comment(self, film_id):
        if self.check_film(film_id):
            stat = 'SELECT * FROM Comments WHERE film_id = (?)'
            return self.conn.execute(stat, film_id).fetchall()
        return []

    def validation_comment(self, film_id, user_id):  # валидация отзыва, если он проходит проверку то comm_check = 1
        x = self.conn.execute('SELECT rating1, rating2, rating3, rating4, rating5, comm_text '
                              'FROM Comments WHERE film_id = (?) and user_id = (?)', (film_id[0], user_id,)).fetchall()
        sr = 0
        for r in x[0][0:5]:
            sr = sr + r
        sr = sr/5
        tokenizer = RegexTokenizer()
        model = FastTextSocialNetworkModel(tokenizer=tokenizer)
        result = model.predict([x[0][5]], k=5)
        dl = result[0]['neutral'] + result[0]['negative'] + result[0]['positive']
        res = 10 * (result[0]['neutral']/dl - result[0]['negative']/dl + result[0]['positive']/dl)
        if abs(sr-res) <= valid_const:
            self.set_comment(film_id, user_id, 'comm_check', 1)
            self.conn.commit()
            self.set_comment(film_id, user_id, 'second_check', 0)
            self.conn.commit()

    def check_notvalid_comm(self, user_id):
        # Если в базе есть непроверенные комментарии других пользователей то достать первый
        stat = 'SELECT film_id, user_id FROM Comments WHERE comm_check = 0 and user_id <> (?);'
        x = self.conn.execute(stat, (user_id,)).fetchall()
        if len(x) != 0:
            return x[0]
        return []

    def resize_second_check(self, film_id, user_id, UPorDOWN):
        stat = 'SELECT second_check FROM Comments WHERE film_id = (?) and user_id = (?);'
        x = self.conn.execute(stat, (film_id[0], user_id,)).fetchall()
        if UPorDOWN == 1:
            res = x[0][0] + 1
        else:
            res = x[0][0] - 1
        stat = 'UPDATE Comments SET second_check = (?) WHERE film_id = (?) and user_id = (?);'
        self.conn.execute(stat, (res, film_id[0], user_id,))
        if res > 2:
            stat = 'UPDATE Comments SET comm_check = 1 WHERE film_id = (?) and user_id = (?);'
            self.conn.execute(stat, (film_id[0], user_id,))
        elif res < -1:
            stat = 'UPDATE Comments SET comm_check = -1 WHERE film_id = (?) and user_id = (?);'
            self.conn.execute(stat, (film_id[0], user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()


def update_film_rating():
    new = BD('BD.sqlite')
    stat = 'SELECT film_id FROM Films'
    res = new.conn.execute(stat).fetchall()
    for film_id in res:
        stat = 'SELECT rating1, rating2, rating3, rating4, rating5, comm_text, comm_check ' \
               'FROM Comments WHERE film_id = (?)'
        result = new.conn.execute(stat, film_id).fetchall()
        le = len(result)
        if le != 0:
            for i in range(1, 6):
                sr = 0
                for rat in result:
                    sr = sr + rat[i - 1]
                sr = sr / le
                new.set_film(film_id, 'rating' + str(i), sr)
