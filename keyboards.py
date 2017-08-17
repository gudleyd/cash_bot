import telebot

lan_choose = telebot.types.ReplyKeyboardMarkup(True)
lan_choose.row('Русский')
lan_choose.row('English')

default_markup = telebot.types.ReplyKeyboardMarkup(True)
default_markup.row(u'\U0001F4D3', 'Excel')
default_markup.row(u'\U0001F527')

settings_markup = telebot.types.ReplyKeyboardMarkup(True)
settings_markup.row(u'\U0001F5D1')
