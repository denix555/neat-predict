#!/usr/bin/env python3

import os
import re
import sys
import time

from binance_api import Binance


API_KEY = 'InFZ6prqSd7IsMkl4ZcfRzG3vagRCGC0N00CRCtLsFykqZGnyPWxMjv6lNPKL2rS'
API_SEC = 'PXm7wGmsLRXwLw8uN0osrDWCA4b6RDzoKcMv50ogba0vEnFayuxg3gxXSRJxBF8t'

bot = Binance(API_KEY,API_SEC)

pair = 'LINKUSDT'
interval = '5m'
limit = 31

filename = 'log_test3c.txt'
os.system("cat /dev/null > log_test3c.txt")

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

        data = info[1]
        end_time = info[1][-1][6] / 1000

        for x in data:
            k = {}

            k[5] = float(x[1])
            k[4] = float(x[2])
            k[3] = float(x[3])
            k[2] = float(x[4])
            k[1] = float(x[5])

            result.append(k)

    return result


def ka(klines):

    rsi7 = 7
    cci7 = 7
    arn25 = 25

    cho3 = []
    cho10 = []

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

        if m == 'up':
            index = arr.index(max(arr))
        elif m == 'down':
            index = arr.index(min(arr))

        arn = ((l - index) / l) * 100

        return arn  

################################## PREPARE ##################################

    len_klines = len(klines)

    for i in range(len_klines):

        c_cho = cho(klines[i][4],klines[i][3],klines[i][2],klines[i][1])

        cho3.append(c_cho)
        cho10.append(c_cho)

        if i >= arn25:

            k = {}
            k['s'] = klines[i][5]
            k['aup'] = aroon([klines[x][2] for x in range(i-arn25,i)][::-1])
            k['ado'] = aroon([klines[x][2] for x in range(i-arn25,i)][::-1],m='down')
            k['r7'] = rsi([klines[x][2] for x in range(i-rsi7,i)])
            k['c7'] = cci([sum([klines[x][4],klines[x][3],klines[x][2]]) / 3 for x in range(i-cci7,i)])
            cho3 = cho3[-len_cho3:]
            c3 = sum(cho3) / len_cho3
            cho10 = cho10[-len_cho10:]
            c10 = sum(cho10) / len_cho10
            k['c31'] = c3-c10
            ind.append(k)

    return ind


def run():

    global buy,stop,profit,buy_price

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

    g = [[3, 0], [2, 1], [1, 1], [5, 1], [2, 1], [3, 1], [4, 0], [3, 0], [1, 1], [2, 0], [3, 0], [2, 1], [2, 1], [2, 0], [5, 1], [3, 1], 32]

    mp = g[-1] / 10

    klines = get_klines()

    if klines:
        d = ka(klines)    

################################### TRADE #####################################

        if not buy:

            action = False
           
            if comp('s',g[0][0],g[0][1],d) and \
               comp('c31',g[1][0],g[1][1],d) and \
               (comp('r7',g[2][0],g[2][1],d) or \
               comp('c7',g[3][0],g[3][1],d)): 
       
                action = True

            elif comp('s',g[4][0],g[4][1],d) and \
                 comp('c31',g[5][0],g[5][1],d) and \
                 (comp('aup',g[6][0],g[6][1],d) or \
                 comp('ado',g[7][0],g[7][1],d)): 

                action = True

            if action:   

                buy_price = d[-1]['s']
                stop = buy_price - (buy_price / 100 * mp)
                buy = True
                print("BUY")

        elif buy:

            action = False

            if comp('s',g[8][0],g[8][1],d) and \
               comp('c31',g[9][0],g[9][1],d) and \
               (comp('r7',g[10][0],g[10][1],d) or \
               comp('c7',g[11][0],g[11][1],d)): 

                action = True

            elif comp('s',g[12][0],g[12][1],d) and \
                 comp('c31',g[13][0],g[13][1],d) and \
                 (comp('aup',g[14][0],g[14][1],d) or \
                 comp('ado',g[15][0],g[15][1],d)): 

                action = True

            elif d[-1]['s'] < stop:
                action = True

            if action:

                percent = ((d[-1]['s'] - buy_price) * 100 / buy_price) - 0.2

                profit += percent
                buy = False

                msg = '{:.2f}'.format(profit) + "\n"
                logger(msg)
                print("SELL")
 

if __name__ == "__main__":

    klines = get_klines()

    if klines:

        while True:    

            time.sleep(1)

            if time.time() > end_time and time.time() - end_time < 10:
                run()

                print("OK")
