#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 12:21:05 2018

@author: chuck
"""

import urllib.request, urllib.parse, urllib.error, datetime, os.path
import pandas as pd
import numpy as np
import sys
from sys import argv


market_cap_cutoff = 75

script, price_update_file, marketcap_update_file = argv



def get_market_data(start_date, market, tag=True):
  """
  market: the full name of the cryptocurrency as spelled on coinmarketcap.com. eg.: 'bitcoin'
  tag: eg.: 'btc', if provided it will add a tag to the name of every column.
  returns: panda DataFrame
  This function will use the coinmarketcap.com url for provided coin/token page. 
  Reads the OHLCV and Market Cap.
  Converts the date format to be readable. 
  Makes sure that the data is consistant by converting non_numeric values to a number very close to 0.
  And finally tags each columns if provided.
  """
  market_data = pd.read_html("https://coinmarketcap.com/currencies/" + market + 
                             "/historical-data/?start="+start_date+"&end="+datetime.date.today().strftime("%Y%m%d"), flavor='html5lib')[0]
  print(market_data)
  market_data = market_data.assign(Date=pd.to_datetime(market_data['Date']))  
  market_data['Volume'] = (pd.to_numeric(market_data['Volume'], errors='coerce').fillna(0))
  if tag:
    market_data.columns = [market_data.columns[0]] + [tag + '_' + i for i in market_data.columns[1:]]
  return market_data


def main():
    coins_list = open("/home/ubuntu/insight/data/top_500_coins.txt", "r")
    coins_dict = {}
    for coin in coins_list:
        coin_split = coin.strip().split("\t")
        name = coin_split[0]
        symbol = coin_split[1]
        coins_dict[symbol.upper()] = name

    price_update = pd.DataFrame(pd.read_csv(price_update_file, sep="\t"))
    marketcap_update = pd.DataFrame(pd.read_csv(marketcap_update_file, sep="\t"))

    asset_list = list(price_update)
    cap_list = list(marketcap_update)
    del asset_list[0]
    del cap_list[0]
    
    price_update = price_update.rename(columns={'Unnamed: 0' :'Date'})
    marketcap_update = marketcap_update.rename(columns={'Unnamed: 0' :'Date'})

    last_update = price_update['Date'].iloc[price_update.shape[0]-1]
    last_update_split = last_update.split("-")
    last_update = datetime.date(int(last_update_split[0]), int(last_update_split[1]), int(last_update_split[2]))

    today = datetime.date.today().strftime("%Y-%m-%d")

    day_count = (datetime.date.today() - datetime.date(int(last_update_split[0]), int(last_update_split[1]), int(last_update_split[2]))).days
    day_count -= 1
    if day_count > 1:

        dates_list = []
        for date in (last_update + datetime.timedelta(n+1) for n in range(day_count)):
            dates_list.append(date.strftime("%Y-%m-%d"))
        
        start_split = dates_list[0].split("-")
        start_date = datetime.date(int(start_split[0]), int(start_split[1]), int(start_split[2])).strftime("%Y%m%d")
        #Create blank numpy dataframe of nxm size, with n = number of dates (day_count), and m = number of cryptos (len(top_market_cap_list))


        crypto_prices = np.zeros((day_count, price_update.shape[1]-1), dtype=float)
        crypto_marketcaps = np.zeros((day_count, marketcap_update.shape[1]-1), dtype=float)


        crypto_prices = pd.DataFrame(crypto_prices, columns = asset_list)
        crypto_marketcaps = pd.DataFrame(crypto_marketcaps, columns = cap_list)

        crypto_prices['Date'] = dates_list
        crypto_marketcaps['Date'] = dates_list

        #crypto_prices.insert(loc=0, column='date', value=dates_list)
        crypto_prices = crypto_prices.set_index('Date')
        crypto_marketcaps = crypto_marketcaps.set_index('Date')

    	#For every crypto asset within the market cap cutoff
        error_list = []
        for asset in asset_list:
            symbol = asset.split("_")[0]
            assetName = coins_dict[symbol]
            print(symbol)
            try:
                coin_info = get_market_data(start_date, assetName, tag=symbol)
                coin_info = coin_info.set_index('Date')
                for date in crypto_prices.index.values:
                    crypto_prices.xs(date)[asset] = coin_info.xs(date)[asset]
                    crypto_marketcaps.xs(date)["%s_Market Cap" % (symbol)] = coin_info.xs(date)["%s_Market Cap" % (symbol)]

            except:
                for date in crypto_prices.index.values:
                    crypto_prices.xs(date)[asset] = 0
                    crypto_marketcaps.xs(date)["%s_Market Cap" % (symbol)] = 0

                error_list.append(assetName)
            

        price_update = price_update.set_index('Date')
        marketcap_update = marketcap_update.set_index('Date')

        price_update = price_update.append(crypto_prices)
        marketcap_update = marketcap_update.append(crypto_marketcaps)

        print(price_update)
        print(marketcap_update)
        today = today.split("-")
        error_log = open("errors_while_updating.txt", "w")
        
        if len(error_list) > 0:
            errors = "\t%s"
            errors = errors * len(error_list)
            error_log.write(str(today) + errors % tuple(error_list))
        else:
            error_log.write("%s\tNoErrors" % (today))
            
        price_update.to_csv(price_update_file, sep='\t')
        marketcap_update.to_csv(marketcap_update_file, sep='\t')
    else:
        print("Prices are up to date.")
    
if __name__ == '__main__':
	main()
