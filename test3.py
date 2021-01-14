#!/usr/bin/env python3

import os
import re
import sys
import time
import copy
import requests

from binance_api import Binance


API_KEY = 'InFZ6prqSd7IsMkl4ZcfRzG3vagRCGC0N00CRCtLsFykqZGnyPWxMjv6lNPKL2rS'
API_SEC = 'PXm7wGmsLRXwLw8uN0osrDWCA4b6RDzoKcMv50ogba0vEnFayuxg3gxXSRJxBF8t'

bot = Binance(API_KEY,API_SEC)

pair = 'BTCUSDT'
interval = '15m'
limit = 10

filename = 'log_test.txt'

start_price = 0.0
min_percent = 1.0
min_rsi3 = 35.0

buy_price = 0.0
profit = 0.0
stop = 0.0

end_time = 0

params = []

buy = False


def logger(msg,log=filename):

    local_dir = os.path.dirname(__file__)
    filename = os.path.join(local_dir,log)
    
    try:
        with open(filename,'a+') as f:
            f.write(msg)
    except Exception as e:
        pass


def rsi(green,red):

    if green:
        all_green = sum(green) / len(green)
    else:
        all_green = 1

    if red:
        all_red = sum(red) / len(red)
    else:
        all_red = 1

    res = round(100 - 100 / (1 + all_green / all_red),1)

    return res


def klines_view():

    global params

    rsi3 = 3
    #line5 = 5
    line8 = 8

    k = {}

    #k['line5'] = round(sum([x[1] for x in klines[-line5:]]) / line5,2)
    k['line8'] = round(sum([x['close'] for x in params]) / line8,2)

    klines = params[-rsi3:]
            
    green = [(x['close'] - x['open']) for x in klines if x['close'] > x['open']]
    red = [(x['open'] - x['close']) for x in klines if x['open'] > x['close']]

    k['rsi3'] = rsi(green,red)

    return k


def get_klines(pair=pair,interval=interval,limit=limit,bot=bot):

    global params,end_time

    result = []
    info = None

    try:
        info = ('klines', bot.klines(symbol=pair,interval=interval,limit=limit))
    except Exception as e:
        logger("\nget_klines() 1: " + str(e) + "\n")
        time.sleep(10)

        try:
            info = ('klines', bot.klines(symbol=pair,interval=interval,limit=limit))
        except Exception as e:
            logger("\nget_klines() 2: " + str(e) + "\n")

    if info:

        data = info[1][-8:]

        end_time = data[-1][6] / 1000

        for x in data:
            k = {}
            k['open'] = float(x[1])
            k['close'] = float(x[4])
            result.append(k)

        params = result


def get_price(pair=pair):

    price = 0.0
    response = None

    addr = "https://api.binance.com/api/v3/ticker/price?symbol="

    try:
        response = requests.get(addr + pair)
    except Exception as e:
        logger("\nget_price() 1: " + str(e) + "\n")
        time.sleep(10)

        try:
            response = requests.get(addr + pair)
        except Exception as e:
            logger("\nget_price() 2: " + str(e) + "\n")
        
    if response:
        data = response.text
        data = re.findall(r'(\d+\.\d+)',data)[0]
        price = float(data)

    return price


def run(price,min_percent=min_percent,min_rsi3=min_rsi3):

    global params,buy,stop,profit,buy_price

    params[-1]['close'] = price

    lines = klines_view()

    msg = str(price) + " " + str(lines['line8'])
    msg += " " + str(lines['rsi3']) + "\n"
    logger(msg)

    if not buy:

        if price > lines['line8'] and lines['rsi3'] > min_rsi3:

            msg = str(price) + " - Покупаем - \n"
            logger(msg)

            buy_price = price
            stop = buy_price - (buy_price / 100 * min_percent)

            buy = True

    elif buy:

        action = False

        if price < lines['line8']:
            action = True

        elif price < stop:
            msg = " - !!!Выход по стопу!!! - \n" 
            logger(msg)
            action = True

        if action:

            real = (price - start_price) * 100 / start_price
            percent = ((price - buy_price) * 100 / buy_price) - 0.2
            profit += percent

            msg = str(price) + " - Продаем - ; " + '{:.2f}'.format(percent) + "%\n"
            msg += " - Профит - " + '{:.2f}'.format(profit) + "%\n"
            msg += " - Профит без торговли - " + '{:.2f}'.format(real) + "%\n"
            
            logger(msg)

            buy = False


if __name__ == "__main__":

    count = 1

    get_klines()
    time.sleep(1)

    start_price = get_price()
    time.sleep(1)

    while True:    
   
        price = get_price()

        if price:
            run(price)

        count += 1
        time.sleep(60)

        if time.time() > end_time:
            get_klines()
            logger("Перезагрузили данные по свечам\n")


