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

INF = 10**18
PRECISION = 10000

dirExcels = 'excels/'
dirDB = 'dataBases/'
bot = telebot.TeleBot(bot_token.token)
BIG_MESSAGE_CONST = 40
NAME_LEN_LIMIT = 32
MAX_COUNT_OF_BARGAINS = 50500

PBS = {}
LIST_PRINTING_QUEUE = Queue()
ONE_DAY_PRINTING_QUEUE = Queue()
ONE_MONTH_PRINTING_QUEUE = Queue()
ONE_YEAR_PRINTING_QUEUE = Queue()
ALL_TIME_PRINTING_QUEUE = Queue()


def start():
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Users(Id INT, Money INT, Date TEXT, Language TEXT, Currency TEXT, Count INT)")
    con.commit()
    con.close()


def is_group_chat(chat):
    return chat.type != "private"


def choose_currency(user_id):
    bot.send_message(user_id, dictionary.lan[read_lan(user_id)][''])


# ЕСЛИ ПЕРЕПИСАТЬ ВСЕ НА MySQL или POSTGRESQL ТО БУДЕТ ЛЕТАТЬ
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
timers = {'/one_day': 5 * 60,
          '/one_month': 15 * 60,
          '/one_year': 60 * 60,
          '/all_time': 24 * 60 * 60}


def create_excel(user_id, period):
    global PBS
    last_excels[user_id][period] = time.time()
    now_date = date()
    lan = read_lan(user_id)
    curSymbol = local_syms[read_currency(user_id)]
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

    if len(data) == 0:
        bot.send_message(user_id, dictionary.lan[lan]['m_emptyHistory'])
        PBS[user_id] = 1
        return
    file_name = '{}_{}.xlsx'.format(user_id, period[1:len(period)])
    workbook = xlsxwriter.Workbook(dirExcels + file_name, {'constant_memory' : True})
    bold = workbook.add_format({'bold': True})

    all_in_one_table = workbook.add_worksheet(dictionary.lan[lan]['m_all_in_one'])
    all_in_one_table.write(0, 0, dictionary.lan[lan]['m_name'], bold)
    all_in_one_table.write(0, 1, dictionary.lan[lan]['m_real_price'], bold)
    all_in_one_table.write(0, 2, dictionary.lan[lan]['m_real_currency'], bold)
    all_in_one_table.write(0, 3, dictionary.lan[lan]['m_price'].format(curSymbol), bold)
    all_in_one_table.write(0, 4, dictionary.lan[lan]['m_date'], bold)

    plus_table = workbook.add_worksheet('+')
    plus_table.write(0, 0, dictionary.lan[lan]['m_name'], bold)
    plus_table.write(0, 1, dictionary.lan[lan]['m_real_price'], bold)
    plus_table.write(0, 2, dictionary.lan[lan]['m_real_currency'], bold)
    plus_table.write(0, 3, dictionary.lan[lan]['m_price'].format(curSymbol), bold)
    plus_table.write(0, 4, dictionary.lan[lan]['m_date'], bold)

    minus_table = workbook.add_worksheet('-')
    minus_table.write(0, 0, dictionary.lan[lan]['m_name'], bold)
    minus_table.write(0, 1, dictionary.lan[lan]['m_real_price'], bold)
    minus_table.write(0, 2, dictionary.lan[lan]['m_real_currency'], bold)
    minus_table.write(0, 3, dictionary.lan[lan]['m_price'].format(curSymbol), bold)
    minus_table.write(0, 4, dictionary.lan[lan]['m_date'], bold)

    i = 1
    p_i = 1
    m_i = 1

    startPeriod = data[0][4]
    finishPeriod = data[len(data) - 1][4]
    max_m = 0
    max_m_name = ''
    max_p = 0
    max_p_name = ''

    p_sum = 0
    m_sum = 0

    for row in data:
        all_in_one_table.write(i, 0, row[0])
        all_in_one_table.write(i, 1, -row[2] / PRECISION)
        all_in_one_table.write(i, 2, row[3])
        all_in_one_table.write(i, 3, row[1] / PRECISION)
        all_in_one_table.write(i, 4, row[4])
        if row[1] >= 0:
            if max_p == 0:
                max_p = row[1]
                max_p_name = row[0]
            elif max_p < row[1]:
                max_p = row[1]
                max_p_name = row[0]
            plus_table.write(p_i, 0, row[0])
            plus_table.write(p_i, 1, -row[2] / PRECISION)
            plus_table.write(p_i, 2, row[3])
            plus_table.write(p_i, 3, row[1] / PRECISION)
            plus_table.write(p_i, 4, row[4])
            p_i += 1
            p_sum += row[1]
        else:
            if max_m == 0:
                max_m = row[1]
                max_m_name = row[0]
            elif max_m < abs(row[1]):
                max_m = abs(row[1])
                max_m_name = row[0]
            minus_table.write(m_i, 0, row[0])
            minus_table.write(m_i, 1, -row[2] / PRECISION)
            minus_table.write(m_i, 2, row[3])
            minus_table.write(m_i, 3, row[1] / PRECISION)
            minus_table.write(m_i, 4, row[4])
            m_i += 1
            m_sum += -row[1]
        i += 1

    max_p /= PRECISION
    max_m /= PRECISION
    m_sum /= PRECISION
    p_sum /= PRECISION

    all_in_one_table.write(i + 1, 2, dictionary.lan[lan]['m_total'])
    all_in_one_table.write_formula(i + 1, 3, "=SUM(D1:D{})".format(i))

    plus_table.write(p_i + 1, 2, dictionary.lan[lan]['m_total'])
    plus_table.write_formula(p_i + 1, 3, "=SUM(D1:D{})".format(p_i))

    minus_table.write(m_i + 1, 2, dictionary.lan[lan]['m_total'])
    minus_table.write_formula(m_i + 1, 3, "=SUM(D1:D{})".format(m_i))
    workbook.close()

    bot.send_message(user_id, dictionary.lan[lan]['m_fast_info'].format(startPeriod, finishPeriod, m_sum, curSymbol, p_sum, curSymbol, max_m_name, max_m, curSymbol, max_p_name, max_p, curSymbol))
    f = open(dirExcels + file_name, 'rb')
    bot.send_chat_action(user_id, 'upload_document')
    bot.send_document(user_id, f)
    f.close()

    os.remove(dirExcels + file_name)
    PBS[user_id] = 1
    last_excels[user_id][period] = time.time()


def add_bargain(user_id, cash, real_price, name, currency):
    now_date = date()
    now_year = int(now_date[:4])
    now_month = int(now_date[5:7])
    now_day = int(now_date[-2:])
    lan = read_lan(user_id)
    money = read_money(user_id)
    if money + cash > INF:
        bot.send_message(user_id, dictionary.lan[lan]['m_money_limit'])
        return
    update('user.db', 'Users', 'Money', money - cash, user_id)
    c = read_count(user_id)
    if c > MAX_COUNT_OF_BARGAINS:
        bot.send_message(user_id, dictionary.lan[lan]['m_bargains_limit'])
        return
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
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
        realPrice = int(float(mesWords[len(mesWords) - 2]) * PRECISION)
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
    if bargainName == '? ':
        bot.send_message(id, str(price / PRECISION) + ' ' + realVal)
        return
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
    mainText = dictionary.lan[lan]['m_mon'] + str(a[0] / PRECISION) + ' ' + local_syms[realCurrency] + '\n\n' + dictionary.lan[lan]['m_lastBars'] + "\n"
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
            realBar = " ({} {})".format(sign + str(abs(row[2] / PRECISION)), local_syms[row[3]])
        ans = st + "\t" + sign + str(abs(row[1] / PRECISION)) + ' ' + local_syms[realCurrency] + realBar + "\n" + ans
    ans = mainText + ans
    bot.send_message(user_id, ans, reply_markup=keyboards.default_markup)


@bot.message_handler(commands=['help'])
def handle_message(message):
    lan = read_lan(message.chat.id)
    bot.send_message(message.chat.id, dictionary.lan[lan]['m_help'])


@bot.message_handler(commands=['contact'])
def handle_message(message):
    bot.send_message(message.chat.id, '@gudleyd')


@bot.message_handler(commands=['info'])
def handle_message(message):
    bot.send_message(message.chat.id, 'Bot icon from www.freepik.com\nCurrency from https://www.cbr-xml-daily.ru/')


@bot.message_handler(commands=['start'])
def handle_message(message):
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS '" + str(message.chat.id) + "' (Id INT, Bargain TEXT, Value REAL, InputValue REAL, Currency TEXT, Date TEXT, Date_day INT, Date_month INT, Date_year INT)")
    con.commit()
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM Users WHERE id = ?", (str(message.chat.id), ))
    a = cur.fetchall()
    if len(a) == 0:
        cur.execute("INSERT INTO Users(Id, Money, Date, Language, Currency, Count) VALUES(?, ?, ?, 'Русский', 'RUB', ?)",
                    (str(message.chat.id), 0, date(), 0))
    con.commit()
    cur.close()
    con.close()
    if is_group_chat(message.chat):
        bot.send_message(message.chat.id, dictionary.lan[read_lan(message.chat.id)]['m_ready'])
    else:
        bot.send_message(message.chat.id, dictionary.lan[read_lan(message.chat.id)]['m_ready'],
                         reply_markup=keyboards.default_markup)


def delete_history(user_id, lan):
    update_money(user_id, 0)
    del_hist(user_id)
    bot.send_message(user_id, dictionary.lan[lan]['m_del_his'], reply_markup=keyboards.default_markup)


@bot.message_handler(commands=['one_day'])
def handle_message(message):
    global PBS, last_excels
    user_id = str(message.chat.id)
    if PBS.get(user_id) == None:
        PBS[user_id] = 1
    if PBS[user_id] == 1:
        if last_excels.get(user_id) == None:
            last_excels[user_id] = {}
            for name in timers.keys():
                last_excels[user_id][name] = 0
        if last_excels[user_id]['/one_day'] + timers['/one_day'] <= time.time():
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_got_in_queue'])
            ONE_DAY_PRINTING_QUEUE.put((user_id, message.text))
            PBS[user_id] = 0
        else:
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_excelTimer'].format('one_day', int(last_excels[user_id]['/one_day'] + timers['/one_day'] - time.time())))

    else:
        bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_in_queue'])


@bot.message_handler(commands=['one_month'])
def handle_message(message):
    global PBS, last_excels
    user_id = str(message.chat.id)
    if PBS.get(user_id) == None:
        PBS[user_id] = 1
    if PBS[user_id] == 1:
        if last_excels.get(user_id) == None:
            last_excels[user_id] = {}
            for name in timers.keys():
                last_excels[user_id][name] = 0
        if last_excels[user_id]['/one_month'] + timers['/one_month'] <= time.time():
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_got_in_queue'])
            ONE_MONTH_PRINTING_QUEUE.put((user_id, message.text))
            PBS[user_id] = 0
        else:
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_excelTimer'].format('one_month', int(last_excels[user_id]['/one_month'] + timers['/one_month'] - time.time())))
    else:
        bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_in_queue'])


@bot.message_handler(commands=['one_year'])
def handle_message(message):
    global PBS, last_excels
    user_id = str(message.chat.id)
    if PBS.get(user_id) == None:
        PBS[user_id] = 1
    if PBS[user_id] == 1:
        if last_excels.get(user_id) == None:
            last_excels[user_id] = {}
            for name in timers.keys():
                last_excels[user_id][name] = 0
        if last_excels[user_id]['/one_year'] + timers['/one_year'] <= time.time():
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_got_in_queue'])
            ONE_YEAR_PRINTING_QUEUE.put((user_id, message.text))
            PBS[user_id] = 0
        else:
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_excelTimer'].format('one_year', int(last_excels[user_id]['/one_year'] + timers['/one_year'] - time.time())))
    else:
        bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_in_queue'])


@bot.message_handler(commands=['all_time'])
def handle_message(message):
    global PBS, last_excels
    user_id = str(message.chat.id)
    if PBS.get(user_id) == None:
        PBS[user_id] = 1
    if PBS[user_id] == 1:
        if last_excels.get(user_id) == None:
            last_excels[user_id] = {}
            for name in timers.keys():
                last_excels[user_id][name] = 0
        if last_excels[user_id]['/all_time'] + timers['/all_time'] <= time.time():
            ALL_TIME_PRINTING_QUEUE.put((user_id, message.text))
            PBS[user_id] = 0
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_got_in_queue'])
        else:
            bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_excelTimer'].format('all_time', int(last_excels[user_id]['/all_time'] + timers['/all_time'] - time.time())))
    else:
        bot.send_message(user_id, dictionary.lan[read_lan(user_id)]['m_in_queue'])


@bot.message_handler(commands=['val_RUB', 'val_KZT', 'val_EUR', 'val_USD'])
def handle_message(message):
    user_id = str(message.chat.id)
    lan = read_lan(user_id)
    cnt = read_count(user_id)
    if cnt == 0:
        currency = message.text[-3:]
        change_currency(user_id, currency)
        bot.send_message(user_id, dictionary.lan[lan]["m_changedCurrency"].format(currency))
    else:
        bot.send_message(user_id, dictionary.lan[lan]['m_not_empty_history_curchg'])


@bot.message_handler(commands=['excel'])
def handle_message(message):
    user_id = str(message.chat.id)
    lan = read_lan(user_id)
    mesText = dictionary.lan[lan]['m_ExcelChoose'].format('/one_day', '/one_month', '/one_year', '/all_time')
    bot.send_message(user_id, mesText)


@bot.message_handler(commands=['list'])
def handle_message(message):
    user_id = str(message.chat.id)
    LIST_PRINTING_QUEUE.put(user_id)
    PBS[user_id] = 1


@bot.message_handler(regexp='/nb *')
def handle_message(message):
    user_id = str(message.chat.id)
    lan = read_lan(user_id)
    txt = message.text[3:]
    if len(txt) < 1:
        bot.send_message(user_id, dictionary.lan[lan]['m_badResponse'])
        return
    if len(txt) > 0 and txt[0] == ' ':
        txt = txt[1:]
    new_bargain(message.chat.id, txt, lan)


@bot.message_handler(commands=['chg'])
def handle_message(message):
    user_id = str(message.chat.id)
    lan = read_lan(user_id)
    txt = message.text[5:]
    new_bargain(message.chat.id, txt, lan)


@bot.message_handler(commands=['delete_history'])
def handle_message(message):
    user_id = str(message.chat.id)
    lan = read_lan(user_id)
    delete_history(user_id, lan)


@bot.message_handler(commands=['currency'])
def handle_message(message):
    bot.send_message(message.chat.id, "/val_USD$\n/val_EUR€\n/val_RUB₽\n/val_KZT₸")


start()
TAKE_PRICES_DELAY = 600
lastTakePrices = time.time()
takePrices()


def one_day_queue():
    while True:
        element = ONE_DAY_PRINTING_QUEUE.get()
        create_excel(element[0], element[1])


def one_month_queue():
    while True:
        element = ONE_MONTH_PRINTING_QUEUE.get()
        create_excel(element[0], element[1])


def one_year_queue():
    while True:
        element = ONE_YEAR_PRINTING_QUEUE.get()
        create_excel(element[0], element[1])


def all_time_queue():
    while True:
        element = ALL_TIME_PRINTING_QUEUE.get()
        create_excel(element[0], element[1])


def list_print_update():
    while True:
        element = LIST_PRINTING_QUEUE.get()
        list_print(element)


one_day_queue_update_thread = threading.Thread(target=one_day_queue, daemon=True)
one_day_queue_update_thread.start()
one_month_queue_update_thread = threading.Thread(target=one_month_queue, daemon=True)
one_month_queue_update_thread.start()
one_year_queue_update_thread = threading.Thread(target=one_year_queue, daemon=True)
one_year_queue_update_thread.start()
all_time_queue_update_thread = threading.Thread(target=all_time_queue, daemon=True)
all_time_queue_update_thread.start()
list_print_queue_update = threading.Thread(target=list_print_update, daemon=True)
list_print_queue_update.start()


@bot.message_handler(func=lambda message: (not is_group_chat(message.chat)) or message.text[2] == '? ', content_types=['text'])
def handle_message(message):
    user_id = str(message.chat.id)
    try:
        global lastTakePrices, LIST_PRINTING_QUEUE
        cur_time = time.time()
        if cur_time - lastTakePrices < TAKE_PRICES_DELAY:
            takePrices()
            lastTakePrices = cur_time
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
            change_lan(user_id, 'Русский')
        elif curMesText == 'Русский':
            change_lan(user_id, 'Русский')
        else:
            new_bargain(message.chat.id, message.text, lan)
    except:
        error(user_id)


LIST_PRINTING_QUEUE.join()
ONE_DAY_PRINTING_QUEUE.join()
ONE_MONTH_PRINTING_QUEUE.join()
ONE_YEAR_PRINTING_QUEUE.join()
ALL_TIME_PRINTING_QUEUE.join()

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except:
        continue
