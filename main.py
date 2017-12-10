# https://vk.com/mynumberisnone

import telebot
import sqlite3
import time
import datetime
import bot_token
import keyboards
import dictionary
import xlsxwriter
import threading
import os
from queue import Queue

from exchange import symbols, convert, takePrices, local_syms

dir = ''
bot = telebot.TeleBot(bot_token.token)
BIG_MESSAGE_CONST = 40
NAME_LEN_LIMIT = 32
MAX_COUNT_OF_BARGAINS = 100000

PBS = {}
LIST_PRINTING_QUEUE = Queue()
ONE_DAY_PRINTING_QUEUE = Queue()
ONE_MONTH_PRINTING_QUEUE = Queue()
ONE_YEAR_PRINTING_QUEUE = Queue()


def start():
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Users(Id INT, Money INT, Date TEXT, Language TEXT, Currency TEXT, Count INT)")
    con.commit()
    con.close()

def choose_currency(user_id):
    bot.send_message(user_id, dictionary.lan[read_lan(user_id)][''])


def read(data_base_name, table_name, fields_to_read, user_id, sign="=", all=False):
    data = []
    with sqlite3.connect(data_base_name) as con:
        cur = con.cursor()
        request = str("SELECT {} FROM '".format(fields_to_read) + table_name + "' WHERE id {} {}".format(sign, user_id))
        cur.execute(request)
        if all:
            data = cur.fetchall()
        else:
            data = cur.fetchone()
        con.commit()
    return data


def read_count(user_id):
    req = read("user.db", "Users", "Count", str(user_id))
    return req[0]


def read_lan(user_id):
    request = read(data_base_name="user.db", table_name="Users", fields_to_read="Language", user_id=user_id)
    return request[0]


def read_money(user_id):
    request = read(data_base_name="user.db", table_name="Users", fields_to_read="Money", user_id=user_id)
    return request[0]


def read_currency(user_id):
    request = read(data_base_name="user.db", table_name="Users", fields_to_read="Currency", user_id=user_id)
    return request[0]


def read_PosToChanCurrency(user_id):
    request = read(data_base_name="user.db", table_name="Users", fields_to_read="PosToChanCurrency", user_id=user_id)
    return request[0]


def read_price(user_id, c):
    request = read(data_base_name="bar.db", table_name=str(user_id), fields_to_read="Value", user_id=c)
    return request[0]


def update(data_base_name, table_name, field_to_update, value, user_id, condition="id = "):
    try:
        with sqlite3.connect(data_base_name) as con:
            cur = con.cursor()
            request = str("UPDATE '" + table_name + "' SET {} = {} WHERE {}{} ".format(field_to_update, value, condition, user_id))
            cur.execute(request)
            con.commit()
        return True
    except:
        return False


def update_money(user_id, value):
    request = update(data_base_name="user.db", table_name="Users", field_to_update="Money", value=value, user_id=user_id)
    return request


def change_lan(user_id, language):
    request = update(data_base_name="user.db", table_name="Users", field_to_update="Language", value="'{}'".format(language), user_id=user_id)
    bot.send_message(user_id, dictionary.lan[language]['m_languageChosen'], reply_markup=keyboards.default_markup)
    return request


def change_count(user_id, value):
    request = update(data_base_name="user.db", table_name="Users", field_to_update="Count", value=value, user_id=user_id)
    return request


def change_currency(user_id, value):
    request = update(data_base_name="user.db", table_name="Users", field_to_update="Currency", value="'{}'".format(value), user_id=user_id)
    return request


def change_posToChanCurrency(user_id, value):
    request = update(data_base_name="user.db", table_name="Users", field_to_update="PosToChanCurrency", value=value, user_id=user_id)
    return request


def error(user_id):
    bot.send_message(user_id, dictionary.lan['error'])


def del_hist(user_id):
    try:
        con = sqlite3.connect('bar.db')
        cur = con.cursor()
        cur.execute("DROP TABLE '" + str(user_id) + "'")
        cur.execute("CREATE TABLE '" + str(user_id) + "' (Id INT, Bargain TEXT, Value REAL, InputValue REAL, Currency TEXT, Date TEXT, Date_day INT, Date_month INT, Date_year INT)")
        con.commit()
        cur.close()
        con.close()
        change_count(user_id, 0)
        change_posToChanCurrency(user_id, 1)
    except:
        error(user_id)


def date():
    unix = int(time.time())
    date_now = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d'))
    return date_now


last_excels = {}
timers = {'one_month': 15 * 60,
          'three_months': 30 * 60,
          'all_time': 5 * 60 * 60}


def create_excel(user_id, period):
    if user_id == '202403359':
        time.sleep(15)
    now_date = date()
    lan = read_lan(user_id)
    data = []
    if period == '/all_time':
        with sqlite3.connect('bar.db') as con:
            cur = con.cursor()
            request = str("SELECT Bargain, Value, InputValue, Currency, Date FROM '" + str(user_id) + "'")
            cur.execute(request)
            data = cur.fetchall()
            con.commit()
    elif period == '/one_month':
        with sqlite3.connect('bar.db') as con:
            cur = con.cursor()
            request = str("SELECT Bargain, Value, InputValue, Currency, Date FROM '" + str(user_id) +
                          "' WHERE Date_month == {} AND Date_year == {}".format(now_date[5:7], now_date[:4]))
            cur.execute(request)
            data = cur.fetchall()
            con.commit()
    elif period == '/one_year':
        with sqlite3.connect('bar.db') as con:
            cur = con.cursor()
            request = str("SELECT Bargain, Value, InputValue, Currency, Date FROM '" + str(user_id) +
                          "' WHERE Date_year == {}".format(now_date[:4]))
            cur.execute(request)
            data = cur.fetchall()
            con.commit()
    elif period == '/one_day':
        with sqlite3.connect('bar.db') as con:
            cur = con.cursor()
            request = str("SELECT Bargain, Value, InputValue, Currency, Date FROM '" + str(user_id) +
                          "' WHERE Date_day == {} AND Date_month == {} AND Date_year == {}".format(now_date[-2:], now_date[5:7], now_date[:4]))
            cur.execute(request)
            data = cur.fetchall()
            con.commit()

    file_name = '{}_{}.xlsx'.format(user_id, period[1:len(period)])
    workbook = xlsxwriter.Workbook(file_name, {'constant_memory' : True})
    bold = workbook.add_format({'bold': True})

    all_in_one_table = workbook.add_worksheet(dictionary.lan[lan]['m_all_in_one'])
    all_in_one_table.write(0, 0, dictionary.lan[lan]['m_name'], bold)
    all_in_one_table.write(0, 1, dictionary.lan[lan]['m_real_price'], bold)
    all_in_one_table.write(0, 2, dictionary.lan[lan]['m_real_currency'], bold)
    all_in_one_table.write(0, 3, dictionary.lan[lan]['m_price'], bold)
    all_in_one_table.write(0, 4, dictionary.lan[lan]['m_date'], bold)

    plus_table = workbook.add_worksheet('+')
    plus_table.write(0, 0, dictionary.lan[lan]['m_name'], bold)
    plus_table.write(0, 1, dictionary.lan[lan]['m_real_price'], bold)
    plus_table.write(0, 2, dictionary.lan[lan]['m_real_currency'], bold)
    plus_table.write(0, 3, dictionary.lan[lan]['m_price'], bold)
    plus_table.write(0, 4, dictionary.lan[lan]['m_date'], bold)

    minus_table = workbook.add_worksheet('-')
    minus_table.write(0, 0, dictionary.lan[lan]['m_name'], bold)
    minus_table.write(0, 1, dictionary.lan[lan]['m_real_price'], bold)
    minus_table.write(0, 2, dictionary.lan[lan]['m_real_currency'], bold)
    minus_table.write(0, 3, dictionary.lan[lan]['m_price'], bold)
    minus_table.write(0, 4, dictionary.lan[lan]['m_date'], bold)

    i = 1
    p_i = 1
    m_i = 1
    for row in data:
        all_in_one_table.write(i, 0, row[0])
        all_in_one_table.write(i, 1, row[2])
        all_in_one_table.write(i, 2, row[3])
        all_in_one_table.write(i, 3, row[1])
        all_in_one_table.write(i, 4, row[4])
        if row[1] >= 0:
            plus_table.write(p_i, 0, row[0])
            plus_table.write(p_i, 1, row[2])
            plus_table.write(p_i, 2, row[3])
            plus_table.write(p_i, 3, row[1])
            plus_table.write(p_i, 4, row[4])
            p_i += 1
        else:
            minus_table.write(m_i, 0, row[0])
            minus_table.write(m_i, 1, row[2])
            minus_table.write(m_i, 2, row[3])
            minus_table.write(m_i, 3, row[1])
            minus_table.write(m_i, 4, row[4])
            m_i += 1
        i += 1
    all_in_one_table.write(i + 1, 0, dictionary.lan[lan]['m_total'])
    all_in_one_table.write_formula(i + 1, 1, "=SUM(B1:B{})".format(i))

    plus_table.write(p_i + 1, 0, dictionary.lan[lan]['m_total'])
    plus_table.write_formula(p_i + 1, 1, "=SUM(B1:B{})".format(p_i))

    minus_table.write(m_i + 1, 0, dictionary.lan[lan]['m_total'])
    minus_table.write_formula(m_i + 1, 1, "=SUM(B1:B{})".format(m_i))
    workbook.close()

    f = open(file_name, 'rb')
    bot.send_document(user_id, f)
    f.close()

    os.remove(file_name)


def add_bargain(user_id, cash, real_price, name, currency):
    now_date = date()
    now_year = int(now_date[:4])
    now_month = int(now_date[5:7])
    now_day = int(now_date[-2:])
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT Money FROM Users WHERE id = ?", (str(user_id),))
    m = cur.fetchone()
    money = m[0]
    cur.execute("UPDATE Users SET money = ? WHERE id = ?", (money - cash, str(user_id),))
    con.commit()
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    c = read_count(user_id)
    cur.execute(
        "INSERT INTO '" + str(user_id) + "' (Id, Bargain, Value, Currency, InputValue, Date, Date_day, Date_month, Date_year) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (c + 1, name, -cash, currency, real_price, now_date, now_day, now_month, now_year, ))
    change_count(user_id, c + 1)
    con.commit()
    cur.close()
    con.close()


def new_bargain(id, message_text, lan):
    if len(message_text) > BIG_MESSAGE_CONST:
        bot.send_message(id, dictionary.lan[lan]['m_bigMessage'])
        return
    realVal = read_currency(id)
    convertVal = realVal
    mesWords = message_text.split()
    if mesWords[len(mesWords) - 1] in symbols:
        convertVal = symbols[mesWords[len(mesWords) - 1]]
    else:
        mesWords.append('XXX')
    realPrice = 0
    priceStr = mesWords[len(mesWords) - 2]
    try:
        realPrice = float(mesWords[len(mesWords) - 2])
    except:
        bot.send_message(id, dictionary.lan[lan]['m_badResponse'])
        return
    if priceStr[0] == '+':
        realPrice = -1 * abs(realPrice)
    else:
        realPrice = abs(realPrice)
    bargainName = ""
    i = 0
    while i < len(mesWords) - 2 and len(bargainName) < NAME_LEN_LIMIT:
        bargainName += mesWords[i] + ' '
        i += 1
    price = int(convert(realPrice, realVal, convertVal))
    add_bargain(id, price, realPrice, bargainName, convertVal)


def delete_one(user_id, lan):
    c = read_count(user_id)
    if c == 0:
        bot.send_message(user_id, dictionary.lan[lan]['m_emptyHistory'])
        return
    m = read_money(user_id)
    p = read_price(user_id, c)
    update_money(user_id, m - p)
    change_count(user_id, c - 1)
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    cur.execute("DELETE FROM '" + str(user_id) + "' WHERE Id = {}".format(c))
    con.commit()
    cur.close()
    con.close()
    bot.send_message(user_id, dictionary.lan[lan]['m_deleted'])


def list_print(user_id):
    lan = read_lan(user_id)
    a = read("user.db", "Users", "Money", user_id)
    realCurrency = read_currency(user_id)
    mainText = dictionary.lan[lan]['m_mon'] + str(a[0]) + ' ' + local_syms[realCurrency] + '\n\n' + dictionary.lan[lan]['m_lastBars'] + "\n"
    ans = ""
    c = read_count(user_id)
    rows = read(data_base_name="bar.db", table_name=str(user_id), fields_to_read="Bargain, Value, InputValue, Currency", user_id=max(0, c - 15), sign=">=", all=True)
    for row in rows:
        st = row[0]
        if len(row[0]) > 10:
            st = st[:10] + '..'
        if row[1] > 0:
            sign = "+"
        else:
            sign = "-"
        realBar = ""
        if row[3] != realCurrency:
            realBar = " ({} {})".format(sign + str(abs(row[2])), local_syms[row[3]])
        ans = st + "\t" + sign + str(abs(row[1])) + ' ' + local_syms[realCurrency] + realBar + "\n" + ans
    ans = mainText + ans
    bot.send_message(user_id, ans, reply_markup=keyboards.default_markup)



@bot.message_handler(commands=['help'])
def handle_message(message):
    lan = read_lan(message.from_user.id)
    bot.send_message(message.from_user.id, dictionary.lan[lan]['m_help'])


@bot.message_handler(commands=['contact'])
def handle_message(message):
    bot.send_message(message.from_user.id, '@gudleyd')


@bot.message_handler(commands=['info'])
def handle_message(message):
    bot.send_message(message.from_user.id, 'Bot icon from www.freepik.com')


@bot.message_handler(commands=['start'])
def handle_message(message):
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS '" + str(message.from_user.id) + "' (Id INT, Bargain TEXT, Value REAL, InputValue REAL, Currency TEXT, Date TEXT, Date_day INT, Date_month INT, Date_year INT)")
    con.commit()
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM Users WHERE id = ?", (str(message.from_user.id), ))
    a = cur.fetchall()
    if len(a) == 0:
        cur.execute("INSERT INTO Users(Id, Money, Date, Language, Currency, Count) VALUES(?, ?, ?, 'Русский', 'RUB', ?)",
                    (str(message.from_user.id), 0, date(), 0))
    con.commit()
    cur.close()
    con.close()
    bot.send_message(message.from_user.id, dictionary.lan[read_lan(message.from_user.id)]['m_ready'], reply_markup=keyboards.lan_choose)


def delete_history(user_id, lan):
    update_money(user_id, 0)
    del_hist(user_id)
    bot.send_message(user_id, dictionary.lan[lan]['m_del_his'], reply_markup=keyboards.default_markup)


@bot.message_handler(commands=['one_day'])
def handle_message(message):
    user_id = str(message.from_user.id)
    if PBS[user_id] == 1:
        ONE_DAY_PRINTING_QUEUE.put((user_id, message.text))
        PBS[user_id] = 0
    else:
        print('No permisition')


@bot.message_handler(commands=['one_month'])
def handle_message(message):
    user_id = str(message.from_user.id)
    if PBS[user_id] == 1:
        ONE_MONTH_PRINTING_QUEUE.put((user_id, message.text))
        PBS[user_id] = 0
    else:
        print('No permisition')


@bot.message_handler(commands=['one_year'])
def handle_message(message):
    user_id = str(message.from_user.id)
    if PBS[user_id] == 1:
        ONE_YEAR_PRINTING_QUEUE.put((user_id, message.text))
        PBS[user_id] = 0
    else:
        print('No permisition')


@bot.message_handler(commands=['val_RUB', 'val_KZT', 'val_EUR', 'val_USD'])
def handle_message(message):
    user_id = str(message.from_user.id)
    lan = read_lan(user_id)
    cnt = read_count(user_id)
    if cnt == 0:
        currency = message.text[-3:]
        change_currency(user_id, currency)
        bot.send_message(user_id, dictionary.lan[lan]["m_changedCurrency"].format(currency))
    else:
        bot.send_message(user_id, dictionary.lan[lan]['m_not_empty_history_curchg'])


@bot.message_handler(commands=['currency'])
def handle_message(message):
    bot.send_message(message.from_user.id, "/val_USD$\n/val_EUR€\n/val_RUB₽\n/val_KZT₸")


start()
TAKE_PRICES_DELAY = 600
lastTakePrices = time.time()
takePrices()


def one_day_queue():
    while True:
        element = ONE_DAY_PRINTING_QUEUE.get()
        if element[0] == "237345588":
            time.sleep(15)
        create_excel(element[0], element[1])
        PBS[element[0]] = 1


def one_month_queue():
    while True:
        element = ONE_MONTH_PRINTING_QUEUE.get()
        if element[0] == "237345588":
            time.sleep(15)
        create_excel(element[0], element[1])
        PBS[element[0]] = 1


def one_year_queue():
    while True:
        element = ONE_YEAR_PRINTING_QUEUE.get()
        if element[0] == "237345588":
            time.sleep(15)
        create_excel(element[0], element[1])
        PBS[element[0]] = 1


def list_print_update():
    while True:
        element = LIST_PRINTING_QUEUE.get()
        if element == "237345588":
            time.sleep(15)
        list_print(element)
        PBS[element] = 1


one_day_queue_update_thread = threading.Thread(target=one_day_queue, daemon=True)
one_day_queue_update_thread.start()
one_month_queue_update_thread = threading.Thread(target=one_month_queue, daemon=True)
one_month_queue_update_thread.start()
one_year_queue_update_thread = threading.Thread(target=one_year_queue, daemon=True)
one_year_queue_update_thread.start()
list_print_queue_update = threading.Thread(target=list_print_update, daemon=True)
list_print_queue_update.start()


@bot.message_handler(content_types=['text'])
def handle_message(message):
    global lastTakePrices, LIST_PRINTING_QUEUE
    cur_time = time.time()
    if cur_time - lastTakePrices < TAKE_PRICES_DELAY:
        takePrices()
        lastTakePrices = cur_time
    user_id = str(message.from_user.id)
    print(user_id)
    lan = read_lan(user_id)
    curMesText = message.text
    if curMesText == u'\U0001F519':
        bot.send_message(user_id, dictionary.lan[lan]['m_back'], reply_markup=keyboards.default_markup)
    elif curMesText == 'Excel':
        mesText = dictionary.lan[lan]['m_ExcelChoose'].format('/one_day', '/one_month', '/one_year', '/all_time')
        bot.send_message(user_id, mesText)
    elif curMesText == dictionary.lan[lan]['b_his']:
        LIST_PRINTING_QUEUE.put(user_id)
        PBS[user_id] = 1
    elif curMesText == '⇦':
        delete_one(user_id, lan)
    elif curMesText == dictionary.lan[lan]['b_set']:
        bot.send_message(user_id, message.text, reply_markup=keyboards.settings_markup)
    elif curMesText == dictionary.lan[lan]['b_del_his']:
        delete_history(user_id, lan)
    elif curMesText == 'English':
        change_lan(user_id, 'English')
    elif curMesText == 'Русский':
        change_lan(user_id, 'Русский')
    else:
        new_bargain(message.from_user.id, message.text, lan)


LIST_PRINTING_QUEUE.join()
ONE_DAY_PRINTING_QUEUE.join()
ONE_MONTH_PRINTING_QUEUE.join()
ONE_YEAR_PRINTING_QUEUE.join()

bot.polling(none_stop=True, interval=0)
