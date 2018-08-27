import requests

prices = {}


local_syms = {}
local_syms['UAH'] = '₴'
local_syms['RUB'] = '₽'
local_syms['EUR'] = '€'
local_syms['USD'] = '$'
local_syms['GBP'] = '£'
local_syms["JPY"] = '¥'
local_syms["KZT"] = '₸'

symbols = {}


def takePrices():
    req = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
    valutes = req.json()['Valute']
    prices['RUB'] = 1
    for v in valutes:
        prices[v] = float(valutes[v]['Value'])
        try:
            local_syms[v] == 'test'
        except:
            local_syms[v] = v
    for i in local_syms:
        symbols[local_syms[i]] = i
        symbols[i] = i


def convert(value, to, fr):
    if fr == to:
        return value
    if fr in symbols and to in symbols:
        inRubs = value * prices[fr]
        return float(inRubs / prices[to])
    else:
        return "Bad valutes"
