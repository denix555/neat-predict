#!/usr/bin/env python3

import re
import os
import sys
import time
import requests


pair = "BNBBTC"
limit = 4

n_truncate = {"BNBBTC":7,"BTCUSDT":2}
data = []


def truncate(d,n):
    return int(d * 10**n) / 10**n


def high_level(price,n):
    return truncate(price + (price / 100 * 0.25), n)


def low_level(price,n):
    return truncate(price - (price / 100 * 0.25), n)
    

def buy(price):
    pass


def sell(price):
    pass


def take_profit(buy,price):
    return round((price - buy) * 100 / buy,2)


def get_price(pair):
    price = ''
    link = "https://api.binance.com/api/v3/ticker/price?symbol="

    try:
        response = requests.get(link + pair)
        res = response.text
        price = re.findall(r'(\d+\.\d+)',res)[0]
        price = float(price)

    except Exception as e:
        print('')
        print(e)
        print('')

    return price


def create_trade(price):
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
        print(e)


def run(price):
    global data,pair,limit

    if not data or (data and price <= data[-1]['low']):
        #buy(price)

        trade = create_trade(price)
        data.append(trade)

        logger(time.ctime(time.time()) + ": Pair - " + pair + "; Buy; Price = " + str(price))
        logger(str(data) + '\n')

        if len(data) > limit-1:
            if pair == "BNBBTC":
                pair = "BTCUSDT"

            elif pair == "BTCUSDT":
                pair = "BNBBTC"

            data = []

    elif data and price >= data[-1]['high']:
        #sell(price)

        logger(time.ctime(time.time()) + ": Pair - " + pair + "; Sell; Price = " + str(price) + "; Profit = " + str(take_profit(data[-1]['buy'],price)) + "%")
        
        if len(data) == 1:
            #buy(price)

            trade = create_trade(price)
            data.insert(0,trade)

            logger(time.ctime(time.time()) + ": Pair - " + pair + "; Buy; Price = " + str(price))

        data.remove(data[-1])

        logger(str(data) + '\n')


if __name__ == "__main__":

    while True:
        price = get_price(pair)

        if price:
            run(price)
        
            #t = time.ctime(time.time())
            #t = re.findall(r'(\d+:\d+):\d+',t)[0]

            #print(t + '\t' + pair + '\t' + str(price))

        time.sleep(60)


