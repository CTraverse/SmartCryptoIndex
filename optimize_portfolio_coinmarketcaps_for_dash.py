#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 13:54:52 2018

@author: chuck
"""

import pandas as pd
import numpy as np
import os


cap_cutoff = 15


price_data = '/home/ubuntu/insight/data/coinmarketcaps_prices_Sep29.csv'
market_cap_data = '/home/ubuntu/insight/data/coinmarketcaps_market_caps_Sep29.csv'

days_back = 0
contextWindow = 14
portfolio_window = 14

historicalPrices = pd.DataFrame(pd.read_csv(price_data, sep = '\t'))
historicalMarketCaps = pd.DataFrame(pd.read_csv(market_cap_data, sep = '\t'))


### Create dictionary of coin names and symbols

namesymbol_dict = {}

coin_directory = '/home/ubuntu/insight/data/Sep29'

coin_files = os.listdir(coin_directory)

for coin in coin_files:

    if '.py' not in coin:
        temp = pd.DataFrame(pd.read_csv('/home/ubuntu/insight/data/coin_histories/%s' % (coin))).set_index("Date")
        coinName = coin.split("_price")[0]
        symbol = list(temp)[1].split("_")[0]
        namesymbol_dict[symbol] = coinName


########################################3


#rename column names to just symbols
historicalPrices.columns = [x.split("_")[0] for x in list(historicalPrices)]
historicalMarketCaps.columns = [x.split("_")[0] for x in list(historicalMarketCaps)]


colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#000000']


        
timeSlicePrice = historicalPrices.iloc[len(historicalPrices)-14:len(historicalPrices)]

timeSlicePrice_NaNs = timeSlicePrice.replace(0, pd.np.nan).replace("-", pd.np.nan)
NaN_cols = timeSlicePrice_NaNs.columns[timeSlicePrice_NaNs.isna().any()].tolist()
timeSlicePrice_cleaned = timeSlicePrice_NaNs.drop(NaN_cols, axis=1)
timeSlicePrice_cleaned = timeSlicePrice_cleaned.drop(['Unnamed: 0'], axis=1).apply(pd.to_numeric)


timeSliceMarketCaps = historicalMarketCaps.iloc[len(historicalPrices)-14:len(historicalPrices)].reset_index(drop=True)
timeSliceMarketCaps_NaNs = timeSliceMarketCaps.replace(0, pd.np.nan).replace("-", pd.np.nan)
NaN_cols = timeSliceMarketCaps_NaNs.columns[timeSliceMarketCaps_NaNs.isna().any()].tolist()
timeSliceMarketCaps_cleaned = timeSliceMarketCaps_NaNs.drop(NaN_cols, axis=1)
timeSliceMarketCaps_cleaned = timeSliceMarketCaps_cleaned.drop(['Unnamed: 0'], axis=1).apply(pd.to_numeric)

timeSliceMarketCaps_sorted = timeSliceMarketCaps_cleaned.reindex_axis(timeSliceMarketCaps_cleaned.mean().sort_values(ascending=False).index, axis=1)

top_MarketCaps = timeSliceMarketCaps_sorted.iloc[:,0:cap_cutoff]

current_MarketCap = top_MarketCaps.iloc[13]

priceSlice = timeSlicePrice_cleaned[list(top_MarketCaps)]

current_prices = priceSlice.iloc[13]

table_out = pd.concat([current_prices, current_MarketCap], axis=1).reset_index()

table_out.columns = ['Asset Name (Asset Symbol)', 'Price', 'Market Cap']

for i in range(table_out.shape[0]):

    table_out['Asset Name (Asset Symbol)'][i] = "%s (%s)" % (namesymbol_dict[table_out['Asset Name (Asset Symbol)'][i]], table_out['Asset Name (Asset Symbol)'][i])
table_out.loc[-1] = ['Asset Name (Asset Symbol)', 'Price', 'Market Cap']
table_out.index = table_out.index + 1  # shifting index
table_out.sort_index(inplace=True) 

table_out.to_csv('/home/ubuntu/insight/data/table_for_dash.txt', sep="\t", index=False)

for i in range(priceSlice.shape[1]):
    asset_name = priceSlice.columns[i]
    column_mean = priceSlice[asset_name].mean()
    column_std = priceSlice[asset_name].std()
    priceSlice[asset_name] = (priceSlice[priceSlice.columns[i]] - column_mean) / column_std    


col_names = list(priceSlice)


    
portfolioSlice = priceSlice.iloc[len(priceSlice)-portfolio_window:len(priceSlice)]

assets_out_list = []
assets_out_Sharpes = []
assets_list = list(top_MarketCaps)

for cluster in [assets_list]:

    cluster_Sharpes = []
    for asset in cluster:

        asset_prices = priceSlice[asset]
        
        asset_return = (asset_prices.iloc[len(asset_prices)-1]/asset_prices.iloc[0] - 1)
        yesterdays_price = asset_prices.iloc[0:len(asset_prices) - 1].reset_index(drop=True)
        todays_price = asset_prices.iloc[1:len(asset_prices)].reset_index(drop=True)
        
        asset_return = ((todays_price / yesterdays_price) - 1)
        asset_volatility = asset_return.std()
        mean_asset_return = asset_return.mean()

        asset_Sharpe = mean_asset_return - asset_volatility ** 2

        cluster_Sharpes.append([asset, mean_asset_return, asset_volatility, asset_Sharpe])
        
    cluster_Sharpes = sorted(cluster_Sharpes, key = lambda x:x[3], reverse=True)

    cluster_out = cluster_Sharpes

    for asset in cluster_out:
        assets_out_Sharpes.append(asset)
    for asset in cluster_out:
        assets_out_list.append(asset[0])

to_test = pd.DataFrame(assets_out_Sharpes)
to_test.columns=['asset', 'return', 'volatility', 'Sharpe']

nassets = to_test.shape[0]
results_df = to_test['asset']
results_list = []

n_portfolios = 75000
results_array = np.zeros((1 + nassets, n_portfolios))

for p in range(n_portfolios):
    weights = np.random.random(nassets)
    #Dividing by the sum of the weights brings the total sum of weights to 1
    weights /= np.sum(weights)
    w = np.array(weights)
    Sharpes = to_test['Sharpe'] * w
    Volatility = to_test['volatility'] * w
    volatility_sum = Volatility.sum()
    Sharpes_sum = Sharpes.sum()

    results_array[0, p] = Sharpes_sum
    
    for i, w in enumerate(weights):
        results_array[1 + i, p] = w


columns = ['Sharpe'] + assets_out_list
# convert results array to Pandas DataFrame
results_frame = pd.DataFrame(np.transpose(results_array),
                                 columns=columns)    


results_sorted = results_frame.sort_values(by='Sharpe', ascending=False)
portfolio_out = results_sorted.iloc[0:10].mean()

print(portfolio_out)

portfolio_out.to_csv("/home/ubuntu/insight/data/portfolio_for_dash.txt", sep = "\t")




    

