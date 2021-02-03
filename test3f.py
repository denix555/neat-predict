#!/usr/bin/env python3

import os
import re
import sys
import time
import json
import requests


pair = 'LTCUSDT'
interval = '5m'
limit = 40

filename = 'log_test3f.txt'
os.system("cat /dev/null > log_test3f.txt")

buy_price1 = 0.0
profit1 = 0.0
buy_price2 = 0.0
profit2 = 0.0
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


def best_price(pair=pair,m='buy'):

    addr = "https://api.binance.com/api/v3/ticker/bookTicker?symbol="

    price = 0.0
    response = None

    try:
        response = requests.get(addr + pair)

    except Exception as e:
        logger("\nbest_price() 1: " + str(e) + "\n")

        time.sleep(10)

        try:
            response = requests.get(addr + pair)

        except Exception as e:
            logger("\nbest_price() 2: " + str(e) + "\n")

    if response:

        res = json.loads(response.text)

        if m == 'buy':
            price = float(res['askPrice'])
        elif m == 'sell':
            price = float(res['bidPrice'])

    return price


def get_klines(pair=pair,interval=interval,limit=limit):

    global end_time

    result = []
    response = None

    addr = "https://api.binance.com/api/v1/klines?symbol=" + pair
    addr += "&interval=" + interval + "&limit=" + str(limit)

    try:
        response = requests.get(addr)
    except Exception as e:
        logger("\nget_klines() 1: " + str(e) + "\n")

        time.sleep(2)

        try:
            response = requests.get(addr)
        except Exception as e:
            logger("\nget_klines() 2: " + str(e) + "\n")

    if response:

        data = json.loads(response.text)

        end_time = data[-1][6] / 1000

        for x in data:
            k = {}

            k[1] = float(x[1])
            k[2] = float(x[2])
            k[3] = float(x[3])
            k[4] = float(x[4])
            k[5] = float(x[5])

            result.append(k)
        
    return result


def ka(klines):

    rsi7 = 7
    cci7 = 7
    ema11 = 11
    ema25 = 25
    arn25 = 25

    cho3 = []
    cho10 = []
    macd = []

    len_macd = 9
    len_cho3 = 3
    len_cho10 = 10

    ind = []

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


    def aroon(arr,m='up'):
        arn = 0.0
        l = len(arr)
        arr = arr[::-1]

        if m == 'up':
            index = arr.index(max(arr))
        elif m == 'down':
            index = arr.index(min(arr))

        arn = ((l - index) / l) * 100

        return arn  

    def ema(e1,e2,n):
        e = 0.0

        a = 2 / (n + 1)
        e = e1 * a + (1 - a) * e2

        return e
 
################################## PREPARE ##################################

    len_klines = len(klines)

    for i in range(len_klines):

        c_cho = cho(klines[i-1][2],klines[i-1][3],klines[i-1][4],klines[i-1][5])
        cho3.append(c_cho)
        cho10.append(c_cho)

        if i >= arn25:

            k = {}

            k['sma1'] = klines[i-1][4]

            if not ind:
                k['ema11'] = sum([klines[x][4] for x in range(i-ema11,i)]) / ema11
                k['ema25'] = sum([klines[x][4] for x in range(i-ema25,i)]) / ema25
            else:
                k['ema11'] = ema(k['sma1'],ind[-1]['ema11'],ema11)
                k['ema25'] = ema(k['sma1'],ind[-1]['ema25'],ema25)

            macd.append(k['ema11'] - k['ema25'])

            if i >= arn25 + len_macd:
               
                k['arn_up'] = aroon([klines[x][4] for x in range(i-arn25,i)])
                k['arn_down'] = aroon([klines[x][4] for x in range(i-arn25,i)],m='down')
                k['rsi7'] = rsi([klines[x][4] for x in range(i-rsi7,i)])
                k['cci7'] = cci([sum([klines[x][2],klines[x][3],klines[x][4]]) / 3 for x in range(i-cci7,i)])

                cho3 = cho3[-len_cho3:]
                c3 = sum(cho3) / len_cho3
                cho10 = cho10[-len_cho10:]
                c10 = sum(cho10) / len_cho10
                k['cho310'] = c3-c10

                macd = macd[-len_macd:]

                if not ind[-1].get('macd'):
                    k['macd'] = sum(macd) / len_macd
                else:
                    k['macd'] = ema(macd[-1],macd[-2],len_macd)

            ind.append(k)

    return ind


def run():

    global buy,stop,profit1,buy_price1,profit2,buy_price2

################################## FUNCTION ##################################

    def comp(key,n,m,ind):
        res = True

        if m == 1:
            if n == 1:
                pass
            elif n == 2:
                if ind[-1][key] < ind[-2][key]:
                    res = False
            elif n == 3:
                if ind[-1][key] < ind[-2][key] or ind[-2][key] < ind[-3][key]:
                    res = False
            elif n == 4:
                if ind[-1][key] < ind[-2][key] or ind[-2][key] < ind[-3][key] \
                   or ind[-3][key] < ind[-4][key]:
                    res = False
            elif n == 5:
                if ind[-1][key] < ind[-2][key] or ind[-2][key] < ind[-3][key] \
                   or ind[-3][key] < ind[-4][key] or ind[-4][key] < ind[-5][key]:
                    res = False

        elif m == 0:
            if n == 1:
                pass
            elif n == 2:
                if ind[-1][key] > ind[-2][key]:
                    res = False
            elif n == 3:
                if ind[-1][key] > ind[-2][key] or ind[-2][key] > ind[-3][key]:
                    res = False
            elif n == 4:
                if ind[-1][key] > ind[-2][key] or ind[-2][key] > ind[-3][key] \
                   or ind[-3][key] > ind[-4][key]:
                    res = False
            elif n == 5:
                if ind[-1][key] > ind[-2][key] or ind[-2][key] > ind[-3][key] \
                   or ind[-3][key] > ind[-4][key] or ind[-4][key] > ind[-5][key]:
                    res = False

        return res 

################################# END FUNCTION #################################

    g = [[1, 3, 0], [3, 4, 0], [4, 2, 0], [0, 2, 1], [1, 4, 0], [4, 5, 0], [3, 1, 0], [0, 5, 0], [5, 4, 1], [0, 1, 0], [3, 2, 0], [2, 3, 0], [6, 4, 1], [6, 4, 1], [1, 4, 1], [1, 4, 1], 25]

    ms = ['sma1','rsi7','cci7','cho310','macd','arn_up','arn_down']

    mp = g[-1] / 10

    klines = get_klines()

    if klines:
        d = ka(klines)    

################################### TRADE #####################################

        if not buy:

            action = False
           
            if comp(ms[g[0][0]],g[0][1],g[0][2],d) and \
               comp(ms[g[1][0]],g[1][1],g[1][2],d) and \
               (comp(ms[g[2][0]],g[2][1],g[2][2],d) or \
               comp(ms[g[3][0]],g[3][1],g[3][2],d)):
       
                action = True

            elif comp(ms[g[4][0]],g[4][1],g[4][2],d) and \
                 comp(ms[g[5][0]],g[5][1],g[5][2],d) and \
                 comp(ms[g[6][0]],g[6][1],g[6][2],d) and \
                 comp(ms[g[7][0]],g[7][1],g[7][2],d):
       
                action = True

            if action: 

                buy_price1 = d[-1]['sma1']
                stop = buy_price1 - (buy_price1 / 100 * mp)
  
                price = best_price()
                real_msg = ''

                if price:
                    buy_price2 = price
                    real_msg = '{:.2f}'.format(buy_price2)

                buy = True

                msg = "\nBUY - price - " + '{:.2f}'.format(buy_price1) + " ; "
                msg += "real price - " + real_msg + "\n"
                logger(msg)

        elif buy:

            action = False

            if comp(ms[g[8][0]],g[8][1],g[8][2],d) and \
               comp(ms[g[9][0]],g[9][1],g[9][2],d) and \
               (comp(ms[g[10][0]],g[10][1],g[10][2],d) or \
               comp(ms[g[11][0]],g[11][1],g[11][2],d)):
       
                action = True

            elif comp(ms[g[12][0]],g[12][1],g[12][2],d) and \
                 comp(ms[g[13][0]],g[13][1],g[13][2],d) and \
                 comp(ms[g[14][0]],g[14][1],g[14][2],d) and \
                 comp(ms[g[15][0]],g[15][1],g[15][2],d):

                action = True

            elif d[-1]['sma1'] < stop:
                msg = "\nSTOP"
                logger(msg)
                action = True

            if action:
                percent1 = ((d[-1]['sma1'] - buy_price1) * 100 / buy_price1) - 0.2
                profit1 += percent1

                price = best_price(m='sell')
                real_msg = ''

                if price and buy_price2:
                    percent2 = ((price - buy_price2) * 100 / buy_price2) - 0.2
                    profit2 += percent2
                    real_msg = '{:.2f}'.format(price) + " ; real percent - "
                    real_msg += '{:.2f}'.format(percent2) + " ; real profit - "
                    real_msg += '{:.2f}'.format(profit2) 

                msg = "\nSELL - price - " + '{:.2f}'.format(d[-1]['sma1']) + " ; "
                msg += "percent - " + '{:.2f}'.format(percent1) + " ; "
                msg += "profit - " + '{:.2f}'.format(profit1) + "\n"
                msg += "real price - " + real_msg + "\n"
                logger(msg)

                buy = False


if __name__ == "__main__":

    klines = get_klines()

    if klines:

        while True:    

            time.sleep(1)

            if time.time() > end_time and time.time() - end_time < 10:
                run()

