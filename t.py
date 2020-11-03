#!/usr/bin/env python3

import os
import sys
import time
import requests

from train_model import Binance


API_KEY = 'InFZ6prqSd7IsMkl4ZcfRzG3vagRCGC0N00CRCtLsFykqZGnyPWxMjv6lNPKL2rS'
API_SEC = 'PXm7wGmsLRXwLw8uN0osrDWCA4b6RDzoKcMv50ogba0vEnFayuxg3gxXSRJxBF8t'

bot = Binance(API_KEY,API_SEC)

pair = "BTCUSDT"
limit = 5

part = 0.0

n_truncate = {"BNBBTC":7,"BTCUSDT":2,"BNBUSDT":4}
q_truncate = {"BNBBTC":2,"BTCUSDT":6,"BNBUSDT":3}

data = []
qty = []


def truncate(d,n):
    return int(d * 10**n) / 10**n


def mean_price(*prices):
    return sum(prices) / len(prices)


def high_level(price,n,data=data):
    result = 0.0

    if data:
        mean = mean_price(data[0]['buy'],price)
        result = truncate(mean + (mean / 100 * 0.25), n)
    else:
        result = truncate(price + (price / 100 * 0.25), n)

    return result


def low_level(price,n,data=data):
    actions = len(data)
    return truncate(price - (price / 100 * 0.20 * (actions + 1)), n)


def take_profit(buy,price):
    return round((price - buy) * 100 / buy,2)


def get_balance(coin,bot=bot):
    balance = 0.0

    try:
        info = ('account',bot.account())

    except Exception as e:
        print("get_balance() 1: " + str(e) + "\n")

        time.sleep(60)

        try:
            info = ('account',bot.account())

        except Exception as e:
            print("get_balance() 2: " + str(e) + "\n")
            sys.exit()

    coins = info[1]['balances']

    for b in coins:
        if b['asset'] == coin:
            balance = float(b['free'])
            break

    return balance


def get_price(pair):
    link = "https://api.binance.com/api/v3/ticker/price?symbol="

    try:
        response = requests.get(link + pair)

    except Exception as e:
        print("get_price() 1: " + str(e) + "\n")

        time.sleep(60)

        try:
            response = requests.get(link + pair)

        except Exception as e:
            print("get_price() 2: " + str(e) + "\n")
            sys.exit()

    res = response.text
    price = eval(res)['price']
    price = float(price)

    return price


def best_price(pair,mode='buy'):
    link = "https://api.binance.com/api/v3/ticker/bookTicker?symbol="

    try:
        response = requests.get(link + pair)

    except Exception as e:
        print("best_price() 1: " + str(e) + "\n")

        time.sleep(60)

        try:
            response = requests.get(link + pair)

        except Exception as e:
            print("best_price() 2: " + str(e) + "\n")
            sys.exit()

    res = response.text

    if mode == 'buy':
        price = eval(res)['bidPrice']
    elif mode == 'sell':
        price = eval(res)['askPrice']

    price = float(price)

    return price


def buy(bot=bot):
    global pair,part,qty,q_truncate

    result = 0.0

    price = best_price(pair,mode='sell')
    q = truncate(part / price * 0.999,q_truncate[pair])

    try: 
        order = ('createOrder', bot.createOrder(
                 symbol=pair,
                 recvWindow=5000,
                 side='BUY',
                 type='MARKET',
                 quantity=q,
                 newOrderRespType='FULL'
               ))
    except Exception as e:
        print('buy() 1: ' + str(e))

        time.sleep(60)

        price = best_price(pair,mode='sell')
        q = truncate(part / price * 0.999,q_truncate[pair])

        try: 
            order = ('createOrder', bot.createOrder(
                     symbol=pair,
                     recvWindow=5000,
                     side='BUY',
                     type='MARKET',
                     quantity=q,
                     newOrderRespType='FULL'
                   ))
        except Exception as e:
            print('buy() 2: ' + str(e))
            sys.exit()

    if order[1]['status'] == 'FILLED':
        result = float(order[1]['fills'][0]['price'])
        qty.append(q)
    else:
        print('buy(): Order not FILLED')
        sys.exit()

    return result


def sell(parts=1,bot=bot):
    global pair,qty,q_truncate

    result = 0.0

    if parts == 1:
        p = qty.pop()
    elif parts == 2:
        p = qty.pop(0) + qty.pop()

    q = truncate(p * 0.999,q_truncate[pair])

    try: 
        order = ('createOrder', bot.createOrder(
                 symbol=pair,
                 recvWindow=5000,
                 side='SELL',
                 type='MARKET',
                 quantity=q,
                 newOrderRespType='FULL'
               ))
    except Exception as e:
        print('sell() 1: ' + str(e))

        time.sleep(60)

        try: 
            order = ('createOrder', bot.createOrder(
                     symbol=pair,
                     recvWindow=5000,
                     side='SELL',
                     type='MARKET',
                     quantity=q,
                     newOrderRespType='FULL'
                   ))
        except Exception as e:
            print('sell() 2: ' + str(e))
            sys.exit()

    if order[1]['status'] == 'FILLED':
        result = float(order[1]['fills'][0]['price'])
    else:
        print('sell(): Order not FILLED')
        sys.exit()

    return result


def create_trade(price):
    global pair,n_truncate
    trade = {}

    trade['buy'] = price
    trade['high'] = high_level(price,n_truncate[pair])
    trade['low'] = low_level(price,n_truncate[pair])

    return trade


def logger(msg,log='log_trade.txt'):
    local_dir = os.path.dirname(__file__)
    filename = os.path.join(local_dir,log)
    
    try:
        with open(filename,'a+') as f:
            f.write(msg + '\n')
    except Exception as e:
        print("logger() 1: " + str(e) + "\n")


def run(price):
    global pair,limit,part,n_truncate,data

    if not data:
        balance = get_balance("USDT")
        part = balance / limit
        result = buy()
        trade = create_trade(result)
        data.append(trade)

    if price <= data[-1]['low'] and len(data) < limit:
        result = buy()
        trade = create_trade(result)
        data.append(trade)

        logger(time.ctime(time.time()) + ": Buy; Price = " + str(result))
        logger(str(data) + '\n')

    elif price >= data[-1]['high']:

        if len(data) > 1:
            result = sell(parts=2)
            data.remove(data[0])
        else:
            result = sell()

        mean = data[-1]['high'] - data[-1]['high'] / 100 * 0.25
        profit = take_profit(mean,result)
        data.remove(data[-1])

        logger(time.ctime(time.time()) + ": Sell; Price = " + str(result) + "; Profit = " + str(profit) + "%")
        
        if data:
            if len(data) > 1:
                mean = mean_price(data[0]['buy'],data[-1]['buy'])
                data[-1]['high'] = mean + mean / 100 * 0.25
            elif len(data) == 1:
                data[-1]['high'] = data[-1]['buy'] + data[-1]['buy'] / 100 * 0.25

            logger(str(data) + '\n')
        else:
            logger("")


if __name__ == "__main__":

    while True:
        price = get_price(pair)

        if price:
            run(price)
        
        time.sleep(60)

