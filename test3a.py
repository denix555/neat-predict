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

pair = 'LINKUSDT'
interval = '5m'
limit = 30

filename = 'log_test3a.txt'
os.system("cat /dev/null > log_test3a.txt")

start_price = 0.0
min_percent = 1.0

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
        data = info[1][:-1]

        for x in data:
            k = {}
            k['open'] = float(x[1])
            k['high'] = float(x[2])
            k['low'] = float(x[3])
            k['close'] = float(x[4])
            k['volume'] = float(x[5])
            result.append(k)

        result = result[::-1]

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

            percent = ((price - buy_price) * 100 / buy_price) - 0.2
            profit += percent

            msg = "\n - !!!STOP!!! - \n" 
            msg += str(price) + " - SELL - ; " + '{:.2f}'.format(percent)
            msg += "%\n - PROFIT - " + '{:.2f}'.format(profit) + "%\n"
            
            logger(msg)

            buy = False


def run(min_percent=min_percent):

    global buy,stop,profit,buy_price

#################################### VARS ####################################

    rsi7 = 7
    cci7 = 7
    cho3 = 3
    cho10 = 10
    
    len_d = 5

################################### DATA ######################################

    ins = ['sma1','cho310','rsi7','cci7']

    g = [[3, 4, 0], [0, 5, 1], [3, 2, 0], [3, 1, 1], [3, 4, 0], [0, 4, 1], [2, 1, 1], [1, 2, 1], [1, 2, 0], [1, 2, 0], [0, 2, 1], [0, 5, 0], [2, 1, 1], [1, 2, 0], [2, 3, 0], [3, 4, 1]]

################################## FUNCTIONS ##################################

    def rsi(arr):

        up = []
        down = []

        l = len(arr) - 1

        for i in range(l):
            r = arr[i+1] - arr[i]

            if r >= 0:
                up.append(r)
            else:
                down.append(r * -1)        

        if up:
            up_result = sum(up) / len(up)
        else:
            up_result = 1

        if down:
            down_result = sum(down) / len(down)
        else:
            down_result = 1

        res = 100 - 100 / (1 + up_result / down_result)

        return res

    def cci(tp):
        
        l = len(tp)
        sma = sum(tp) / l

        stp = [x - sma for x in tp]
        d = sum([x for x in stp if x > 0])
        d += sum([(x*-1) for x in stp if x < 0])
        d = d / l

        c = 1 / 0.015 * ((tp[-1] - sma) / d)

        return c

    def cho(high,low,close,volume):
        c = 0.0

        try:
            c = ((close - low) - (high - close)) / (high - low) * volume
        except Exception:
            pass

        return c

    def comp(key,n,m,ind):
        res = True

        if m == 1:
            if n == 1:
                pass
            elif n == 2:
                if ind[0][key] <= ind[1][key]:
                    res = False
            elif n == 3:
                if ind[0][key] <= ind[1][key] or ind[1][key] <= ind[2][key]:
                    res = False
            elif n == 4:
                if ind[0][key] <= ind[1][key] or ind[1][key] <= ind[2][key] \
                   or ind[2][key] <= ind[3][key]:
                    res = False
            elif n == 5:
                if ind[0][key] <= ind[1][key] or ind[1][key] <= ind[2][key] \
                   or ind[2][key] <= ind[3][key] or ind[3][key] <= ind[4][key]:
                    res = False

        elif m == 0:
            if n == 1:
                pass
            elif n == 2:
                if ind[0][key] >= ind[1][key]:
                    res = False
            elif n == 3:
                if ind[0][key] >= ind[1][key] or ind[1][key] >= ind[2][key]:
                    res = False
            elif n == 4:
                if ind[0][key] >= ind[1][key] or ind[1][key] >= ind[2][key] \
                   or ind[2][key] >= ind[3][key]:
                    res = False
            elif n == 5:
                if ind[0][key] >= ind[1][key] or ind[1][key] >= ind[2][key] \
                   or ind[2][key] >= ind[3][key] or ind[3][key] >= ind[4][key]:
                    res = False

        return res 

################################## PREPARE ##################################

    klines = get_klines()
 
    if klines:
        d = []

        for i in range(len_d):
            k = {}

            k['sma1'] = klines[i]['close']
            k['rsi7'] = rsi([klines[x]['close'] for x in range(i,i+rsi7)])
            k['cci7'] = cci([sum([klines[x]['high'],klines[x]['low'],klines[x]['close']]) / 3 for x in range(i,i+cci7)])
            cho_3 = sum([cho(klines[x]['high'],klines[x]['low'],klines[x]['close'],klines[x]['volume']) for x in range(i,i+cho3)]) / cho3
            cho_10 = sum([cho(klines[x]['high'],klines[x]['low'],klines[x]['close'],klines[x]['volume']) for x in range(i,i+cho10)]) / cho10
            k['cho310'] = cho_3 - cho_10

            d.append(k)

################################### TRADE #####################################

        if not buy:

            action = False
           
            if comp(ins[g[0][0]],g[0][1],g[0][2],d) and \
               comp(ins[g[1][0]],g[1][1],g[1][2],d) and \
               comp(ins[g[2][0]],g[2][1],g[2][2],d) and \
               comp(ins[g[3][0]],g[3][1],g[3][2],d): 
       
                action = True

            elif comp(ins[g[4][0]],g[4][1],g[4][2],d) and \
                 comp(ins[g[5][0]],g[5][1],g[5][2],d) and \
                 comp(ins[g[6][0]],g[6][1],g[6][2],d) or \
                 comp(ins[g[7][0]],g[7][1],g[7][2],d): 

                action = True

            if action:   

                buy_price = d[0]['sma1']
                stop = buy_price - (buy_price / 100 * min_percent)
                buy = True

                msg = "\n" + '{:.2f}'.format(buy_price) + " - RUN - BUY \n"
                logger(msg)

        elif buy:

            action = False

            if comp(ins[g[8][0]],g[8][1],g[8][2],d) and \
               comp(ins[g[9][0]],g[9][1],g[9][2],d) and \
               (comp(ins[g[10][0]],g[10][1],g[10][2],d) or \
               comp(ins[g[11][0]],g[11][1],g[11][2],d)): 

                action = True

            elif comp(ins[g[12][0]],g[12][1],g[12][2],d) and \
                 comp(ins[g[13][0]],g[13][1],g[13][2],d) and \
                 (comp(ins[g[14][0]],g[14][1],g[14][2],d) or \
                 comp(ins[g[15][0]],g[15][1],g[15][2],d)): 

                action = True

            elif d[0]['sma1'] < stop:
                msg = "\n - !!!STOP!!! - " 
                logger(msg)
                action = True

            if action:

                percent = ((d[0]['sma1'] - buy_price) * 100 / buy_price) - 0.2

                if percent < (min_percent * -1):
                    percent = (min_percent * -1)

                profit += percent
                buy = False

                msg = "\n" + '{:.2f}'.format(d[0]['sma1']) + " - RUN - SELL ; PROFIT - " 
                msg += '{:.2f}'.format(percent) + "%\n"
                msg += "ALL PROFIT - " + '{:.2f}'.format(profit) + "%\n"
                logger(msg)
 

if __name__ == "__main__":

    count = 1

    first_klines = get_klines()

    if first_klines:

        start_price = first_klines[-1]['close']

        while True:    

            count += 1
   
            time.sleep(1)

            if time.time() > end_time:
                run()

                if not buy:
                    time.sleep(60 * 4)

            if buy and count % 60 == 0:
                stop_loss()

