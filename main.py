#https://vk.com/mynumberis21

import telebot
import sqlite3
import time
import datetime
import bot_token
import keyboards
import dictionary
import xlsxwriter
import threading


dir = r'Excels\\'[:-1]
bot = telebot.TeleBot(bot_token.token)

#Создание таблицы Users, если это первый запуск программы
def create_main_table():
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Users(Id INT, Money INT, Date TEXT, Language TEXT, Count INT)")
    con.commit()
    cur.close()
    con.close()

#Функция вывода ошибки, если покупка введена неправильно
def bar_error(id):
    bot.send_message(id, dictionary.lan[read_lan(id)]['bar_error'],
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
    change_count(id, 0)
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

last_excels = {}
timers = {'one_month': 5 * 60,
          'three_months': 30 * 60,
          'year': 60 * 60,
          'all_time': 5 * 60 * 60}

#Создаем Excel-таблицу
def excelCreating(id, by):
    nowTime = time.time()
    lan = read_lan(id)
    con = sqlite3.connect('bar.db')
    cur = con.cursor()
    cur.execute("SELECT Bargain, Value, Date FROM '" + str(id) + "'")
    rows = cur.fetchall()
    if len(rows) == 0:
        bot.send_message(id, dictionary.lan[lan]['m_emptyHistory'])
        return
    if last_excels.get(id) == None:
        last_excels[id] = {}
        for name in timers.keys():
            last_excels[id][name] = 0
    if nowTime - last_excels[id][by] < timers[by]:
        secs = timers[by] - nowTime + last_excels[id][by]
        h = int(secs // 3600)
        m = int((secs - h * 3600) // 60)
        bot.send_message(id, dictionary.lan[lan]['m_excelTimer'].format(by, h, m, int(secs % 60)))
        return
    else:
        last_excels[id][by] = nowTime
    name = r'{}{}_{}.xlsx'.format(dir, id, by)
    workbook = xlsxwriter.Workbook(name)
    heap = workbook.add_worksheet(dictionary.lan[lan]['m_heap'])
    min = []
    plus = []
    if by == 'one_month':
        fm = rows[len(rows) - 1][2][5:7]
        sm = fm
        heap.write(0, 0, dictionary.lan[lan]['m_name'])
        heap.write(0, 1, dictionary.lan[lan]['m_price'])
        i, j = 0, 1
        sum = 0
        while i < len(rows) and sm == fm:
            if int(rows[len(rows) - 1 - i][1]) > 0:
                plus.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1],  rows[len(rows) - 1 - i][2]))
            else:
                min.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
            heap.write(i, j - 1, rows[len(rows) - 1 - i][0])
            heap.write(i, j, rows[len(rows) - 1 - i][1])
            heap.write(i, j + 1, rows[len(rows) - 1 - i][2])
            sum += int(rows[len(rows) - 1 - i][1])
            if len(rows) - 1 - i < 0:
                break
            sm = rows[len(rows) - 1 - i][2][5:7]
            i += 1
        heap.write(i + 1, 0, dictionary.lan[lan]['m_total'])
        heap.write(i + 1, 1, sum)
    elif by == 'all_time':
        heap.write(0, 0, dictionary.lan[lan]['m_name'])
        heap.write(0, 1, dictionary.lan[lan]['m_price'])
        i, j = 0, 1
        sum = 0
        while i < len(rows):
            if int(rows[len(rows) - 1 - i][1]) > 0:
                plus.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
            else:
                min.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
            heap.write(i, j - 1, rows[len(rows) - 1 - i][0])
            heap.write(i, j, rows[len(rows) - 1 - i][1])
            heap.write(i, j + 1, rows[len(rows) - 1 - i][2])
            sum += int(rows[len(rows) - 1 - i][1])
            if len(rows) - 1 - i < 0:
                break
            i += 1
        heap.write(i + 1, 0, dictionary.lan[lan]['m_total'])
        heap.write(i + 1, 1, sum)
    elif by == 'year':
        fy = rows[len(rows) - 1][2][:4]
        print(fy)
        sy = fy
        heap.write(0, 0, dictionary.lan[lan]['m_name'])
        heap.write(0, 1, dictionary.lan[lan]['m_price'])
        i, j = 0, 1
        sum = 0
        while i < len(rows) and sy == fy:
            if int(rows[len(rows) - 1 - i][1]) > 0:
                plus.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
            else:
                min.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
            heap.write(i, j - 1, rows[len(rows) - 1 - i][0])
            heap.write(i, j, rows[len(rows) - 1 - i][1])
            heap.write(i, j + 1, rows[len(rows) - 1 - i][2])
            sum += int(rows[len(rows) - 1 - i][1])
            if len(rows) - 1 - i < 0:
                break
            sy = rows[len(rows) - 1 - i][2][:4]
            print(sy)
            i += 1
        heap.write(i + 1, 0, dictionary.lan[lan]['m_total'])
        heap.write(i + 1, 1, sum)
    elif by == 'three_months':
        # fm = rows[len(rows) - 1][2][5:7]
        # sm = fm
        # s = 0
        # if int(fm) == 1:
        #     s = 10
        # elif int(fm) == 2:
        #     s = 11
        # elif int(fm) == 3:
        #     s = 12
        # else:
        #     s = int(fm) - 2
        # heap.write(0, 0, dictionary.lan[lan]['m_name'])
        # heap.write(0, 1, dictionary.lan[lan]['m_price'])
        # i, j = 1, 1
        # sum = 0
        # while sm != s:
        #     if int(rows[len(rows) - 1 - i][1]) > 0:
        #         plus.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
        #     else:
        #         min.append((rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][1], rows[len(rows) - 1 - i][2]))
        #     heap.write(i, j - 1, rows[len(rows) - 1 - i][0])
        #     heap.write(i, j, rows[len(rows) - 1 - i][1])
        #     heap.write(i, j + 1, rows[len(rows) - 1 - i][2])
        #     i += 1
        #     sum += int(rows[len(rows) - 1 - i][1])
        #     if len(rows) - 1 - i < 0:
        #         break
        #     sm = rows[len(rows) - 1 - i][2][5:7]
        # heap.write(i + 1, 0, dictionary.lan[lan]['m_total'])
        # heap.write(i + 1, 1, sum)
        bot.send_message(id, 'Заглушка')
        return
    pm = workbook.add_worksheet('+-')
    pm.write(0, 0, dictionary.lan[lan]['m_name'])
    pm.write(0, 1, dictionary.lan[lan]['m_price'])
    i, j = 1, 1
    sum = 0
    for m in min:
        sum += m[1]
        pm.write(i, j - 1, m[0])
        pm.write(i, j, m[1])
        pm.write(i, j + 1, m[2])
        i += 1
    i += 1
    pm.write(i, j - 1, dictionary.lan[lan]['m_total'])
    pm.write(i, j, sum)
    i += 3
    sum2 = 0
    for p in plus:
        sum2 += p[1]
        pm.write(i, j - 1, p[0])
        pm.write(i, j, p[1])
        pm.write(i, j + 1, p[2])
        i += 1
    i += 1
    pm.write(i, j - 1, dictionary.lan[lan]['m_total'])
    pm.write(i, j, sum2)
    pm.write(i + 2, j - 1, dictionary.lan[lan]['m_total'])
    pm.write(i + 2, j, sum2 + sum)
    workbook.close()
    f = open(name, 'rb')
    bot.send_document(id, f)
    f.close()


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
            if len(a[len(a) - 1]) > 12:
                bot.send_message(id, dictionary.lan[read_lan(id)]['m_bigNumber'])
            else:
                if a[len(a) - 1][0] == "+":
                    cash = -abs(cash)
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
                c = read_count(id)
                cur.execute(
                    "INSERT INTO '" + str(id) + "' (Id, Bargain, Value, Date) VALUES(?, ? , ?, ?)",
                    (c + 1, name, -cash, date()))
                change_count(id, c + 1)
                con.commit()
                cur.close()
                con.close()


#Выводим покупки
def list_print(id):
    lan = read_lan(id)
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT Money FROM Users WHERE id = ?", (str(id),))
    a = cur.fetchone()
    mainText = dictionary.lan[read_lan(id)]['m_mon'] + str(a[0]) + u'\U0001F4B5' + '\n\n' + dictionary.lan[lan]['m_lastBars'] + "\n"
    ans = ""
    con.commit()
    con = sqlite3.connect('bar.db')
    with con:
        cur = con.cursor()
        c = read_count(id)
        cur.execute("SELECT Bargain, Value FROM '" + str(id) + "' WHERE Id >= {}".format(str(max(0, c - 15))))
        rows = cur.fetchall()
        for row in rows:
            if row[1] > 0:
                sign = "+"
            else:
                sign = ""
            ans = row[0] + "\t" + sign + str(row[1]) + u'\U0001F4B5' + "\n" + ans
        ans = mainText + ans
        bot.send_message(id, ans, reply_markup=keyboards.default_markup)
    cur.close()
    con.close()


#Смена языка
def change_lan(id, lan):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("UPDATE Users SET Language = ? WHERE Id = ?", (lan, str(id),))
    con.commit()
    bot.send_message(id, "Ok", reply_markup=keyboards.default_markup)
    cur.close()
    con.close()


#Чтение кол-ва покупок
def read_count(id):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT Count FROM Users WHERE id = ?", (str(id),))
    req = cur.fetchone()
    con.commit()
    cur.close()
    con.close()
    return req[0]


#Смена кол-ва покупок
def change_count(id, val):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("UPDATE Users SET Count = ? WHERE Id = ?", (val, str(id),))
    con.commit()
    cur.close()
    con.close()


#Получаем язык
def read_lan(id):
    con = sqlite3.connect('user.db')
    cur = con.cursor()
    cur.execute("SELECT Language FROM Users WHERE id = ?", (str(id),))
    con.commit()
    a = cur.fetchone()
    cur.close()
    con.close()
    return str(a[0])


create_main_table()


@bot.message_handler(commands=['help'])
def handle_message(message):
    lan = read_lan(message.from_user.id)
    bot.send_message(message.from_user.id, dictionary.lan[lan]['m_help'])


@bot.message_handler(commands=['contact'])
def handle_message(message):
    lan = read_lan(message.from_user.id)
    bot.send_message(message.from_user.id, '@van4es0909')


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
    if len(a) == 0:
        cur.execute("INSERT INTO Users(Id, Money, Date, Language, Count) VALUES(?, ?, ?, 'Русский', ?)",
                    (str(message.from_user.id), 0, date(), 0))
    con.commit()
    cur.close()
    con.close()
    bot.send_message(message.from_user.id, dictionary.lan[read_lan(message.from_user.id)]['m_ready'], reply_markup=keyboards.lan_choose)


@bot.message_handler(commands=['ex_year'])
def handle_message(message):
    excelCreating(str(message.from_user.id), 'year')


@bot.message_handler(commands=['ex_1_month'])
def handle_message(message):
    excelCreating(str(message.from_user.id), 'one_month')


@bot.message_handler(commands=['ex_3_months'])
def handle_message(message):
    excelCreating(str(message.from_user.id), 'three_months')


@bot.message_handler(commands=['ex_time'])
def handle_message(message):
    excelCreating(str(message.from_user.id), 'all_time')



@bot.message_handler(content_types=['text'])
def handle_message(message):
    chat_id = message.from_user.id
    curMesText = message.text
    lan = read_lan(chat_id)
    if curMesText  == u'\U0001F519':
        bot.send_message(chat_id, dictionary.lan[lan]['m_back'], reply_markup=keyboards.default_markup)
    elif curMesText == 'Excel':
        mesText = dictionary.lan[lan]['m_ExcelChoose'].format('/ex_1_month', '/ex_3_months', '/ex_year', '/ex_time')
        bot.send_message(chat_id, mesText)
    elif curMesText == dictionary.lan[lan]['b_his']: #История
        list_print(message.from_user.id)
    elif curMesText == dictionary.lan[lan]['b_set']: #Настройки
        bot.send_message(chat_id, message.text, reply_markup=keyboards.settings_markup)
    elif curMesText == dictionary.lan[lan]['b_del_his']: #Удалить историю
        update_money(chat_id, 0)
        del_hist(chat_id)
        bot.send_message(message.from_user.id, dictionary.lan[lan]['m_del_his'], reply_markup=keyboards.default_markup)
    elif curMesText == 'English':
        change_lan(chat_id, 'English')
    elif curMesText == 'Русский':
        change_lan(chat_id, 'Русский')
    else:
        new_bargain(message.from_user.id, message.text)

bot.polling(none_stop=True, interval=0)
