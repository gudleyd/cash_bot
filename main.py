import telebot
import sqlite3
import time
import datetime
import bot_token
import keyboards
import dictionary

bot = telebot.TeleBot(bot_token.token)

#Создание таблицы Users, если это первый запуск программы
def create_main_table():
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Users(Id INT, Money INT, Date TEXT, Language TEXT)")
    con.commit()
    cur.close()
    con.close()

#Функция вывода ошибки, если покупка введена неправильно
def bar_error(id):
    bot.send_message(id, dictionary.lan[receive_lan(id)]['bar_error'],
                     disable_notification=True)

#Функция обновления денег
def update_money(id, value):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("UPDATE Users SET Money = ? WHERE id = ?", (value, str(id),))
    con.commit()
    cur.close()
    con.close()

#Стираем историю
def del_hist(id):
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    cur.execute("DROP TABLE '" + str(id) + "'")
    cur.execute("CREATE TABLE '" + str(id) + "' (Id INT, Bargain TEXT, Value REAL, Date TEXT)")
    con.commit()
    cur.close()
    con.close()

#Получаем дату
def date():
    unix = int(time.time())
    date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d'))
    return date

#Добавляем покупку
def new_bargain(id, message_text):
    a = message_text.split()
    name = ""
    i = 0
    while i < len(a) - 1 and len(name) + len(a[i]) < 15:
        name += a[i] + " "
        i += 1
    if len(name) == 0 or i < 1:
        bar_error(id)
    else:
        try:
            float(a[len(a) - 1])
        except ValueError:
            bar_error(id)
        else:
            cash = float(a[len(a) - 1])
            if (a[len(a) - 1][0] == "+"):
                cash = - abs(cash)
            else:
                cash = abs(cash)
            con = sqlite3.connect('user.db')
            cur = con.cursor()
            cur.execute("SELECT Money FROM Users WHERE id = ?", (str(id),))
            m = cur.fetchone()
            money = m[0]
            cur.execute("UPDATE Users SET money = ? WHERE id = ?", (money - cash, str(id),))
            con.commit()
            con = sqlite3.connect('bar.db')
            cur = con.cursor()
            cur.execute(
                "INSERT INTO '" + str(id) + "' (Id, Bargain, Value, Date) VALUES(NULL, ? , ?, ?)",
                (name, -cash, date()))
            con.commit()
            cur.close()
            con.close()

#Выводим покупки
def list_print(id):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT Money FROM Users WHERE id = ?", (str(id),))
    a = cur.fetchone()
    ans = dictionary.lan[receive_lan(id)]['m_mon'] + str(a[0]) + u'\U0001F4B5' + "\n"
    con.commit()
    con = sqlite3.connect('bar.db')
    with con:
        cur = con.cursor()
        cur.execute("SELECT Bargain, Value FROM '" + str(id) + "'")
        rows = cur.fetchall()
        for row in rows:
            if (row[1] > 0):
                sign = "+"
            else:
                sign = ""
            ans += row[0] + " | " + sign + str(row[1]) + u'\U0001F4B5' + "\n"
        bot.send_message(id, ans, reply_markup=keyboards.default_markup)
    cur.close()
    con.close()

def change_lan(id, lan):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("UPDATE Users SET Language = ? WHERE Id = ?", (lan, str(id),))
    con.commit()
    bot.send_message(id, "Ok", reply_markup=keyboards.default_markup)
    cur.close()
    con.close()

def receive_lan(id):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT Language FROM Users WHERE id = ?", (str(id),))
    con.commit()
    a = cur.fetchone()
    return str(a[0])
    cur.close()
    con.close()

create_main_table()

@bot.message_handler(commands=['start'])
def handle_message(message):
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS '" + str(message.from_user.id) + "' (Id INT, Bargain TEXT, Value REAL, Date TEXT, Date_day INT, Date_month INT, Date_year INT)")
    con.commit()
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM Users WHERE id = ?", (str(message.from_user.id), ))
    a = cur.fetchall()
    if (len(a) == 0):
        cur.execute("INSERT INTO Users(Id, Money, Date, Language) VALUES(?, ?, ?, 'Русский')",
                    (str(message.from_user.id), 0, date()))
    con.commit()
    cur.close()
    con.close()
    bot.send_message(message.from_user.id, dictionary.lan[receive_lan(message.chat.id)]['m_ready'], reply_markup=keyboards.lan_choose)


@bot.message_handler(content_types=['text'])
def handle_message(message):
    if message.text == dictionary.lan[receive_lan(message.chat.id)]['b_his']: #История
        list_print(message.from_user.id)
    elif message.text == dictionary.lan[receive_lan(message.chat.id)]['b_set']: #Настройки
        bot.send_message(message.chat.id, message.text, reply_markup=keyboards.settings_markup)
    elif message.text == dictionary.lan[receive_lan(message.chat.id)]['b_del_his']: #Удалить историю
        update_money(message.chat.id, 0)
        del_hist(message.chat.id)
        bot.send_message(message.from_user.id, dictionary.lan[receive_lan(message.chat.id)]['m_del_his'], reply_markup=keyboards.default_markup)
    elif message.text == 'English':
        change_lan(message.chat.id, 'English')
    elif message.text == 'Русский':
        change_lan(message.chat.id, 'Русский')
    else:
        new_bargain(message.from_user.id, message.text)

bot.polling(none_stop=True, interval=0)