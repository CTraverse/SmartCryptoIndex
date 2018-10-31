#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 12:21:05 2018

@author: chuck
"""

"""
This script updates the master coin dataframe that is stored as a .csv file.
It opens up the coin csv and determines if the price data is up to date.
The master coin file is indexed by date, so it grabs the bottom row date and determiens
how long ago the file was updated. It then grabs the market data for each coin in the dataframe
for the number of days that it hasn't been updated and appends the new market data to the end of the
coins dataframe.
"""

import urllib.request, urllib.parse, urllib.error, datetime, os.path
import pandas as pd
import numpy as np
import sys
from sys import argv

script, price_update_file, marketcap_update_file = argv


#This function finds the market data object for the coin of interest
#This is pulled from the coinmarketcap.com API
def get_market_data(start_date, market, tag=True):
  #Get the market data from the given start date up until todays date
  market_data = pd.read_html("https://coinmarketcap.com/currencies/" + market + 
                             "/historical-data/?start="+start_date+"&end="+datetime.date.today().strftime("%Y%m%d"), flavor='html5lib')[0]

  market_data = market_data.assign(Date=pd.to_datetime(market_data['Date']))
  market_data['Volume'] = (pd.to_numeric(market_data['Volume'], errors='coerce').fillna(0))
  #Tag each type of market data with the coin symbol so that they are unique to the coin
  if tag == True:
    market_data.columns = [market_data.columns[0]] + [tag + '_' + i for i in market_data.columns[1:]]
  return market_data


def main():
    #open up the list of top 500 coins and create a dictionary to convert the coin symbols into coin names
    coins_list = open("/home/ubuntu/insight/data/top_500_coins.txt", "r")
    coins_dict = {}
    for coin in coins_list:
        coin_split = coin.strip().split("\t")
        name = coin_split[0]
        symbol = coin_split[1]
        coins_dict[symbol.upper()] = name
	
    #Open up the coin prices and the coin marketcaps csv files
    price_update = pd.read_csv(price_update_file, sep="\t")
    marketcap_update = pd.read_csv(marketcap_update_file, sep="\t")

    #grab the list of coin symbol names in the price and marketcap dataframes
    asset_list = list(price_update)
    cap_list = list(marketcap_update)
	
    #Delete the first entry because it is the name of the date column
    del asset_list[0]
    del cap_list[0]
    
    #Set the first column of the dataframe equal to 'Date'
    price_update = price_update.rename(columns={'Unnamed: 0' :'Date'})
    marketcap_update = marketcap_update.rename(columns={'Unnamed: 0' :'Date'})

    #Find when the last update occurred, which is the last entry in the dataframe
    last_update = price_update['Date'].iloc[price_update.shape[0]-1]
    last_update_split = last_update.split("-")
    #Convert the last update into a datetime object
    last_update = datetime.date(int(last_update_split[0]), int(last_update_split[1]), int(last_update_split[2]))
    
    #Grab todays date
    today = datetime.date.today().strftime("%Y-%m-%d")

    #Determine how many days it has been since the last update
    day_count = (datetime.date.today() - datetime.date(int(last_update_split[0]), int(last_update_split[1]), int(last_update_split[2]))).days - 1

    #If the dataframes haven't been updated in the past day, update them with the most recent price data
    if day_count > 1:
	#Find all of the dates that haven't been updated yet
        dates_list = []
        for date in (last_update + datetime.timedelta(n+1) for n in range(day_count)):
            dates_list.append(date.strftime("%Y-%m-%d"))
        
	#Grab the date to start getting market data and convert into the correct datetime format recognized by the API
        start_split = dates_list[0].split("-")
        start_date = datetime.date(int(start_split[0]), int(start_split[1]), int(start_split[2])).strftime("%Y%m%d")
       
	#Create blank numpy dataframe of n by m size, 
	#with n = number of dates (day_count), and m = number of cryptos
        crypto_prices = np.zeros((day_count, price_update.shape[1]-1), dtype=float)
        crypto_marketcaps = np.zeros((day_count, marketcap_update.shape[1]-1), dtype=float)

	#Set the column names
        crypto_prices = pd.DataFrame(crypto_prices, columns = asset_list)
        crypto_marketcaps = pd.DataFrame(crypto_marketcaps, columns = cap_list)

	#Enter the dates into the empy dataframe
        crypto_prices['Date'] = dates_list
        crypto_marketcaps['Date'] = dates_list

        #Set the dates as the index for the dataframes
        crypto_prices = crypto_prices.set_index('Date')
        crypto_marketcaps = crypto_marketcaps.set_index('Date')

    	#Sometimes smaller coins won't have information or will be discontinued,
	#So keep a list of coins that we can't find data for
        error_list = []
	#Loop through each coin in the dataframe and get the market data
        for asset in asset_list:
	    #Grab just the symbol name
            symbol = asset.split("_")[0]
	    #Get the coin name from the dictionary we made before
            assetName = coins_dict[symbol]
	    
	    #Try to get the coin data. As mentioned above, sometimes coins will have errors or be discontinued,
	    #so store any erros in a list and enter zeroes into the dataframe for that coin
            try:
		#call the coinmarketcap API function
                coin_info = get_market_data(start_date, assetName, tag=symbol)
		#Set the date as the index so the updated dataframe can be correctly updated
                coin_info = coin_info.set_index('Date')
		#Update the empty dataframe we made above, using the date and asset as the row/column index names
                for date in crypto_prices.index.values:
                    crypto_prices.xs(date)[asset] = coin_info.xs(date)[asset]
                    crypto_marketcaps.xs(date)["%s_Market Cap" % (symbol)] = coin_info.xs(date)["%s_Market Cap" % (symbol)]
	    #If there was an error updating, update the data with zeroes and store the coin in a list to be evaluated later
            except:
                for date in crypto_prices.index.values:
                    crypto_prices.xs(date)[asset] = 0
                    crypto_marketcaps.xs(date)["%s_Market Cap" % (symbol)] = 0

                error_list.append(assetName)
            
        #Set the indexes for the price/marketcap update files as the dates
	#Since they are in the same format as the new market data we grabbed,
	#simply appending the new data to this dataframe will put the data in the correct order
        price_update = price_update.set_index('Date')
        marketcap_update = marketcap_update.set_index('Date')

	#Append the updated data to the existing dataframe
        price_update = price_update.append(crypto_prices)
        marketcap_update = marketcap_update.append(crypto_marketcaps)

	#Add any errors to the running error log
	#Errors only occur on very small coins, so they are extremely unlikely to affect the top 15 cryptos,
	#which are what we are interested in for this project
        today = today.split("-")
        error_log = open("errors_while_updating.txt", "w")
	
        #If there are errors, create a string equal to the number of coins with an error
	#Then write the date and the list of coins to the error file
        if len(error_list) > 0:
            errors = "\t%s"
            errors = errors * len(error_list)
            error_log.write(str(today) + errors % tuple(error_list))
        else:
            error_log.write("%s\tNoErrors" % (today))
            
        price_update.to_csv(price_update_file, sep='\t')
        marketcap_update.to_csv(marketcap_update_file, sep='\t')

    
if __name__ == '__main__':
	main()
