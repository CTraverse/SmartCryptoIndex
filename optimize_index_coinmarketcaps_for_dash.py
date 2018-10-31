#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 13:54:52 2018

@author: chuck
"""

"""
This script will generate an optimized index for the past two weeks of price data in the top 15 cryptocurrencies.
It generates 100,000 random indexes in the top 15 cryptocurrencies and calculates the overall return and volatility
for the past two weeks of price action. It then uses Modern Portfolio Theory to choose the optimal index weights.
This is done using a modified Sharpe ratio, where the volatility is subtracted from the overall return of each asset.
"""


import pandas as pd
import numpy as np
import os


#Create dictionary of coin names and symbols
coin_directory = '/home/ubuntu/insight/data/Sep29'
coin_files = os.listdir(coin_directory)
#Open the dict
namesymbol_dict = {}
#loop through each individual coin file and grab the coin name from the file name
#Then open open up the file and grab the symbol name from a column that contains the correct name
for coin in coin_files:
    coinName = coin.split("_price")[0]
    temp = pd.read_csv('/home/ubuntu/insight/data/coin_histories/%s' % (coin)).set_index("Date")
    symbol = list(temp)[1].split("_")[0]
    namesymbol_dict[symbol] = coinName

    
############################################################################################
## Process the price history and market cap data to be used in the index and a data table ##
############################################################################################

#paths to price and coinmarketcap data
price_data = '/home/ubuntu/insight/data/coinmarketcaps_prices_Sep29.csv'
market_cap_data = '/home/ubuntu/insight/data/coinmarketcaps_market_caps_Sep29.csv'

#Open the prices and marketcap data as pandas dataframes
historicalPrices = pd.read_csv(price_data, sep = '\t')
historicalMarketCaps = pd.read_csv(market_cap_data, sep = '\t')


#rename column names to just symbols
historicalPrices.columns = [x.split("_")[0] for x in list(historicalPrices)]
historicalMarketCaps.columns = [x.split("_")[0] for x in list(historicalMarketCaps)]

#Time window to optimize the indexes for
index_window = 14

#Grab the past 14 days if price history and marketcap data for all coins
timeSlicePrice = historicalPrices.iloc[len(historicalPrices)-index_window:len(historicalPrices)]
timeSliceMarketCaps = historicalMarketCaps.iloc[len(historicalPrices)-index_window:len(historicalPrices)]

#Replace any zeros or '-' with NaN, then drop all NaN columns from the past 14 days.
#This needs to be done because some coins may drop to zero in the market
#However, because we focus on the top 15 coins, this is extremely unlikely to happen to any coins of interest
timeSlicePrice_NaNs = timeSlicePrice.replace(0, pd.np.nan).replace("-", pd.np.nan)
NaN_cols = timeSlicePrice_NaNs.columns[timeSlicePrice_NaNs.isna().any()].tolist()
timeSlicePrice_cleaned = timeSlicePrice_NaNs.drop(NaN_cols, axis=1)
#Drop the date, as it's no longer needed for the rest of the analysis
timeSlicePrice_cleaned = timeSlicePrice_cleaned.drop(['Unnamed: 0'], axis=1).apply(pd.to_numeric)

#### Process Market Caps Data ####

#Replace any zeroes or '-' with NaN, then drop all NaN columns from the past 14 days.
timeSliceMarketCaps_NaNs = timeSliceMarketCaps.replace(0, pd.np.nan).replace("-", pd.np.nan)
NaN_cols = timeSliceMarketCaps_NaNs.columns[timeSliceMarketCaps_NaNs.isna().any()].tolist()
timeSliceMarketCaps_cleaned = timeSliceMarketCaps_NaNs.drop(NaN_cols, axis=1)
#Drop the date, as it's no longer needed for the rest of the analysis
timeSliceMarketCaps_cleaned = timeSliceMarketCaps_cleaned.drop(['Unnamed: 0'], axis=1).apply(pd.to_numeric)

#Sort the market caps columns by the top coins by market cap
#Take the mean of the marketcaps and sort the dataframe by those values
timeSliceMarketCaps_sorted = timeSliceMarketCaps_cleaned.reindex_axis(timeSliceMarketCaps_cleaned.mean().sort_values(ascending=False).index, axis=1)

#The cutoff for coinmarketcaps. In this case, the top 15 are used
cap_cutoff = 15

############################################################################################
################### Generate the table to be used in the dash website ######################
############################################################################################

#Only grab the top 15 coins
top_MarketCaps = timeSliceMarketCaps_sorted.iloc[:,0:cap_cutoff]

#Grab the current marketcaps, which is the last row in the dataframe
current_MarketCap = top_MarketCaps.iloc[13]

#Grab the prices for only the top marketcaps
#Do this by grabbing a list of the top marketcap coins, and take the prices by column names
priceSlice = timeSlicePrice_cleaned[list(top_MarketCaps)]

#Grab the current prices. These will be put into the table on the dash website
current_prices = priceSlice.iloc[13]

#Make the table for the dash website
#Concat the prices and marketcap information
#Create a blank column for the asset name/symbol
table_out = pd.concat([current_prices, current_MarketCap], axis=1).reset_index()
table_out.columns = ['Asset Name (Asset Symbol)', 'Price', 'Market Cap']

#Populate the blank asset name/symbol column with the actual asset names and symbols
for i in range(table_out.shape[0]):
    table_out['Asset Name (Asset Symbol)'][i] = "%s (%s)" % (namesymbol_dict[table_out['Asset Name (Asset Symbol)'][i]], table_out['Asset Name (Asset Symbol)'][i])

#When exporting the table in its current form, the headers don't appear in the Dash table
#To fix this we'll set the last row to be the header names, add 1 to the index, and then sort the table
#so that the column names are the first row in the table
table_out.loc[-1] = ['Asset Name (Asset Symbol)', 'Price', 'Market Cap']
table_out.index = table_out.index + 1  # shifting index
table_out.sort_index(inplace=True) 

#Save the table as a file, which the dash website will then read in
table_out.to_csv('/home/ubuntu/insight/data/table_for_dash.txt', sep="\t", index=False)

############################################################################################
################ Optimize the index for the past two weeks of price data ###################
############################################################################################

#List of all assets in the top 15 cryptocurrencies
assets_list = list(priceSlice)

#Calculate the overall return and volatility for each individual asset for the past two weeks
for asset in assets_list:
    #Grab the prices for the past two weeks for the current asset
    asset_prices = priceSlice[asset]
    
    #Grab yesterday's prices as all prices excluding the last row
    #Grab todays prices as all prices excluding the first row
    #This offets the prices by 1, allowing for easy division of the two columns together
    #to generate the daily return
    yesterdays_price = asset_prices.iloc[0:len(asset_prices) - 1].reset_index(drop=True)
    todays_price = asset_prices.iloc[1:len(asset_prices)].reset_index(drop=True)
    #Subtract 1 so the output is a positive or negative gain/loss relative to the day before
    asset_return = ((todays_price / yesterdays_price) - 1) 
    
    #Calculate volatility as the standard devation of the asset return
    asset_volatility = asset_return.std()
    #Calculate mean asset return over the two week period
    mean_asset_return = asset_return.mean()
    
    #Calculate the modified Sharpe value for each asset
    #This is done by subtracting the squared volatility from mean asset return
    #The squared volatility is a standard baseline in portfolio theory that weights risk.
    #Any higher number than two will weight volatility more, while lower values will weight return more.
    asset_Sharpe = mean_asset_return - asset_volatility ** 2
    
    #store the asset, return, volatility, and Sharpe as a list of lists
    Sharpes_list.append([asset, mean_asset_return, asset_volatility, asset_Sharpe])

#Sort the list of lists by the Sharpe value
Sharpes_list = sorted(Sharpes_list, key = lambda x:x[3], reverse=True)

Sharpes_out = Sharpes_list

#Create a dataframe of what will be tested to determine optimal ratios for the index
to_test = pd.DataFrame(Sharpes_list)
to_test.columns=['asset', 'return', 'volatility', 'Sharpe']

#number of assets to test
num_assets = to_test.shape[0]
#number of portfolios to generate
num_portfolios = 100000
#create a results array that will store each portfolio
results_array = np.zeros((3 + num_assets, num_portfolios))

for index in range(num_portfolios):
    #Generate random weights for each asset
    weights = np.random.random(num_assets)
    #Dividing by the sum of the weights brings the total sum of weights to 1
    weights /= np.sum(weights)
    w = np.array(weights)
    
    #Multiply each Sharpe, return, and volatility value from each individual asset by its corresponding random weight
    Sharpes = to_test['Sharpe'] * w
    Return = to_test['return'] * w
    Volatility = to_test['volatility'] * w
    
    #Sum the Sharpes, return, and volatility to get the overall values for the randomized index
    Sharpes_sum = Sharpes.sum()
    return_sum = Return.sum()
    volatility_sum = Volatility.sum()
    
    #Store the index Sharpes, return, and volatility in the results array
    results_array[0, index] = Sharpes_sum
    results_array[1, index] = return_sum
    results_array[2, index] = volatility_sum
    
    #store the weights of each asset in the results array
    for i, w in enumerate(weights):
        results_array[1 + i, p] = w

#Column names for the results array
columns = ['Sharpe', 'return', 'volatility'] + assets_list
# convert results array to Pandas DataFrame
results_frame = pd.DataFrame(np.transpose(results_array),
                                 columns=columns)    

#Sort the results by the Sharpe values, higher values = optimized for return and volatility
results_sorted = results_frame.sort_values(by='Sharpe', ascending=False)
#Take the mean of the top 10 optimized indexes as the overall optimized index
## Taking the mean performed better than taking the top portfolio
index_out = results_sorted.iloc[0:10].mean()

#Write the index to a file to be used by the dash website
index_out.to_csv("/home/ubuntu/insight/data/index_for_dash.txt", sep = "\t")




    

