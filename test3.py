#!/usr/bin/env python3

import os
import re
import sys
import time
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
min_percent = 1.5

buy_price = 0.0
profit = 0.0
stop = 0.0

end_time = 0

buy = False


def logger(msg,log=filename):

    local_dir = os.path.dirname(__file__)
    filename = os.path.join(local_dir,log)
    
    try:
        with open(filename,'a+') as f:
            f.write(msg)
    except Exception as e:
        pass


def klines_view(params):

    line8 = 8

    k = {}

    k['line1'] = params[-1]['close']
    k['line8'] = round(sum([x['close'] for x in params]) / line8,2)

    return k


def get_klines(pair=pair,interval=interval,limit=limit,bot=bot):

    global end_time

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

        end_time = info[1][-1][6] / 1000
        data = info[1][-9:-1]

        for x in data:
            k = {}
            k['open'] = float(x[1])
            k['close'] = float(x[4])
            result.append(k)

    return result


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


def stop_loss(start_price=start_price,buy_price=buy_price,stop=stop):

    global buy,profit

    price = get_price()

    if price:

        if price < stop:

            real = (price - start_price) * 100 / start_price
            percent = ((price - buy_price) * 100 / buy_price) - 0.2
            profit += percent

            msg = "\n - !!!STOP!!! - \n" 
            msg += str(price) + " - SELL - ; " + '{:.2f}'.format(percent)
            msg += "%\n - PROFIT - " + '{:.2f}'.format(profit) + "%\n"
            msg += " - REAL PROFIT - " + '{:.2f}'.format(real) + "%\n"
            
            logger(msg)

            buy = False


def run(min_percent=min_percent):

    global buy,stop,profit,buy_price

    params = get_klines()
 
    if params:

        lines = klines_view(params)

        msg = str(lines['line1']) + " " + str(lines['line8']) + "\n"
        logger(msg)

        if not buy:

            if lines['line1'] > lines['line8']:

                msg = "\n" + str(lines['line1']) + " - BUY - \n"
                logger(msg)

                buy_price = lines['line1']
                stop = buy_price - (buy_price / 100 * min_percent)

                buy = True

        elif buy:

            action = False

            if lines['line1'] < lines['line8']:
                action = True

            elif lines['line1'] < stop:
                msg = "\n - !!!STOP!!! - " 
                logger(msg)
                action = True

            if action:

                real = (lines['line1'] - start_price) * 100 / start_price
                percent = ((lines['line1'] - buy_price) * 100 / buy_price) - 0.2
                profit += percent

                msg = "\n" + str(lines['line1']) + " - SELL - ; " + '{:.2f}'.format(percent)
                msg += "%\n - PROFIT - " + '{:.2f}'.format(profit) + "%\n"
                msg += " - REAL PROFIT - " + '{:.2f}'.format(real) + "%\n"
            
                logger(msg)

                buy = False


if __name__ == "__main__":

    count = 1

    first_klines = get_klines()

    if first_klines:

        start_price = first_klines[-1]['close']

        while True:    

            count += 1
   
            time.sleep(2)

            if time.time() > end_time:
                run()

                if not buy:
                    time.sleep(60 * 14)

            if buy and count % 15 == 0:
                stop_loss()

