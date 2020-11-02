#!/usr/bin/env python3

import re
import os
import sys
import time
import requests

from train_model import Binance


API_KEY = 'InFZ6prqSd7IsMkl4ZcfRzG3vagRCGC0N00CRCtLsFykqZGnyPWxMjv6lNPKL2rS'
API_SEC = 'PXm7wGmsLRXwLw8uN0osrDWCA4b6RDzoKcMv50ogba0vEnFayuxg3gxXSRJxBF8t'

bot = Binance(API_KEY,API_SEC)

pair = "BNBBTC"
limit = 5

part = 0.0
qty = 0.0

n_truncate = {"BNBBTC":7,"BTCUSDT":2,"BNBUSDT":4}
q_truncate = {"BNBBTC":2,"BTCUSDT":6,"BNBUSDT":3}

data = []


def truncate(d,n):
    return int(d * 10**n) / 10**n


def high_level(price,n):
    return truncate(price + (price / 100 * 0.25), n)


def low_level(price,n):
    return truncate(price - (price / 100 * 0.25), n)


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


def buy(pair=pair,bot=bot):
    global part,qty,q_truncate

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
        qty = q
    else:
        print('buy(): Order not FILLED')
        sys.exit()

    return result


def sell(pair=pair,n=q_truncate[pair],bot=bot):
    global part,qty

    result = 0.0

    q = truncate(qty * 0.999,n)

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


def create_trade(price,buy=True):
    trade = {}

    if buy:
        trade['buy'] = price
    else:
        trade['buy'] = 0.0

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


def run_bnbusdt(price,):
    global pair,limit,part,qty,q_truncate,n_truncate,data

    time.sleep(5)
    price_bnbbtc = get_price("BNBBTC")

    if data[-1]['back'] == 0.0:
        back = high_level(data[-1]['buy'],n_truncate["BNBBTC"])
        data = []
        trade = create_trade(price)
        data.append(trade)
        data[-1]['back'] = back

        logger("run_bnbusdt(): " + time.ctime(time.time()) + ": " + str(data) + "\n")

    if price >= data[-1]['high']:
        result = sell()

        logger("run_bnbusdt(): " + time.ctime(time.time()) + ": Pair - " + pair + "; Sell; Price = " + str(result) + "; Profit = " + str(take_profit(data[-1]['buy'],result)) + "%\n")

        pair = "BTCUSDT"
        balance = get_balance("USDT")
        part = balance / limit
        data = []

    elif price_bnbbtc > data[-1]['back']:
        result = sell(pair="BNBBTC",n=q_truncate["BNBBTC"])
        profit = take_profit(low_level(data[-1]['back'],n_truncate["BNBBTC"]),result)

        logger("run_bnbusdt(): " + time.ctime(time.time()) + ": Pair - BTCUSDT; Sell(back); Price = " + str(result) + "; Profit = " + profit + "%\n")

        pair = "BNBBTC"
        data[-1]['buy'] = result


def run_btcusdt(price):
    global pair,limit,part,n_truncate,data

    if not data:
        trade = create_trade(price,buy=False)
        data.append(trade)

    if price <= data[-1]['low'] or data[-1].get('back'):
        result = buy()

        if data[-1]['buy'] == 0.0:
            data = []

        trade = create_trade(result)
        data.append(trade)

        logger(time.ctime(time.time()) + ": Pair - " + pair + "; Buy; Price = " + str(result))
        logger(str(data) + '\n')

        if len(data) > limit-1:
            pair = "BNBBTC"

    elif price >= data[-1]['high'] and data[-1].get('buy'):
        result = sell()

        logger(time.ctime(time.time()) + ": Pair - " + pair + "; Sell; Price = " + str(result) + "; Profit = " + str(take_profit(data[-1]['buy'],result)) + "%")
        
        if len(data) == 1:
            result = buy()

            trade = create_trade(result)
            data.insert(0,trade)

            logger(time.ctime(time.time()) + ": Pair - " + pair + "; Buy; Price = " + str(result))

        data.remove(data[-1])

        logger(str(data) + '\n')


def run_bnbbtc(price):
    global pair,part,qty,n_truncate,q_truncate,data

    time.sleep(5)
    price_btc = get_price("BTCUSDT")

    if not data:
        trade = create_trade(price,buy=False)
        data.append(trade)
        data[-1]['back'] = high_level(price_btc,n_truncate["BTCUSDT"])

        logger("run_bnbbtc(): " + time.ctime(time.time()) + ": " + str(data) + '\n')

    elif len(data[-1]) < 4:
        mean_price_btc = sum([trade['buy'] for trade in data]) / len(data)
        data = []
        trade = create_trade(price,buy=False)
        data.append(trade)
        data[-1]['low'] = low_level(data[-1]['low'],n_truncate[pair])
        data[-1]['back'] = high_level(mean_price_btc,n_truncate["BTCUSDT"])

        logger("run_bnbbtc(): " + time.ctime(time.time()) + ": " + str(data) + '\n')

    elif data[-1].get('back') == 0.0
        buy_price = data[-1]['buy']
        data = []
        trade = create_trade(buy_price,buy=False)
        data.append(trade)
        data[-1]['back'] = high_level(price_btc,n_truncate["BTCUSDT"])

        logger("run_bnbbtc(): " + time.ctime(time.time()) + ": " + str(data) + '\n')

    if price_btc > data[-1]['back']:
        qty = get_balance("BTC")
        result = sell(pair="BTCUSDT",n=q_truncate["BTCUSDT"])
        profit = take_profit(low_level(data[-1]['back'],n_truncate["BTCUSDT"]),result)

        logger("run_bnbbtc(): " + time.ctime(time.time()) + ": Pair - BTCUSDT; Sell(back); Price = " + str(result) + "; Profit = " + profit + "%\n")

        pair = "BTCUSDT"
        data[-1]['buy'] = 0.0
        balance = get_balance("USDT")
        part = balance / limit

    elif price < data[-1]['low']:
        part = get_balance("BTC")
        result = buy()

        logger("run_bnbbtc(): " + time.ctime(time.time()) + ": Pair - " + pair + "; Buy; Price = " + str(result) + "\n")

        pair = "BNBUSDT"
        data[-1]['buy'] = result 
        data[-1]['back'] = 0.0


if __name__ == "__main__":

    while True:
        price = get_price(pair)

        if price:
            if pair == "BNBBTC":
                run_bnbbtc(price)
            elif pair == "BTCUSDT":
                run_btcusdt(price)
            elif pair == "BNBUSDT":
                run_bnbusdt(price)
        
        time.sleep(60)

