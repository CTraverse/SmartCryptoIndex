#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 19:24:30 2018

@author: chuck
"""



import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import os

app = dash.Dash(__name__)
server = app.server


# read data for tables (one df per table)
price_data = '/home/ubuntu/insight/data/coinmarketcaps_prices_Sep29.csv'
market_cap_data = '/home/ubuntu/insight/data/coinmarketcaps_market_caps_Sep29.csv'



historicalPrices = pd.DataFrame(pd.read_csv(price_data, sep = '\t'))
historicalMarketCaps = pd.DataFrame(pd.read_csv(market_cap_data, sep = '\t'))



colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
          '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', 
          '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', 
          '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080']


portfolio = pd.DataFrame(pd.read_csv("/home/ubuntu/insight/data/portfolio_for_dash.txt", sep="\t"))
portfolio.columns = ['asset', 'proportion']
assets = list(portfolio['asset'])
proportions = list(portfolio['proportion'])

table_df = pd.read_csv("/home/ubuntu/insight/data/table_for_dash.txt", sep="\t")

colors = colors[0:len(assets)]

investment_data = pd.DataFrame(pd.read_csv('/home/ubuntu/insight/data/investment_comparison.csv', sep="\t"))
investment_data.columns = ['Date', 'SmartPortfolio', 'Top15Weighted', 'CoinBase']


# reusable componenets
def make_dash_table(df):
    ''' Return a dash definition of an HTML table for a Pandas dataframe '''
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table


def get_header():
    header = html.Div([

        html.Div([
            html.H5(
                'Executive Summary: Smart Crypto Index', style={'fontSize': 20, 'font-weight': 'bold', 'font-family': 'arial'})
        ], className="twelve columns padded")

    ], className="row gs-header gs-text-header")
    return header


overview = html.Div([  # page 1


        html.Div([

            # Header
            get_header(),
            html.Br([]),

            # Row 3

            html.Div([

                html.Div([
                    html.H6('Product Summary', style={ 'textAlign': 'center', 'fontSize': 16, 'font-weight': 'bold', 'font-family': 'arial'},
                            className="gs-header gs-text-header padded"),

                    html.Br([]),

                    html.P("\
                            Investing in Cryptocurrencies (Crypto assets) can be a difficult process involving extensive research and technical expertise.\n \
                            The Smart Crypto Index analyzes the market to find the top performing coins with the highest Market Cap.\n \
                            An algorithm is deployed to determine the optimal propotions of coins to invest in.\n \
                            The app will automatically re-allocate your funds every two weeks to remain as competitive as possible.\n \
                            The Smart Crypto Index strategy out-performs commonly used Market Cap weighting strategies.", 
                            style={'fontSize': 16, 'textAlign': 'justify', 'font-family': 'arial'}),

                ], className="six columns"),

                html.Div([
                    html.H6(["Top 15 Crypto Assets"], style={ 'textAlign': 'center', 'fontSize': 16, 'font-weight': 'bold', 'font-family': 'arial'},
                            className="gs-header gs-table-header padded"),
                    html.Table(make_dash_table(table_df), style={'fontSize': 12, 'font-family': 'arial'})
                ], className="six columns"),

            ], className="row "),

            # Row 4

            html.Div([

                html.Div([
                    html.H6('Current Smart Crypto Index Allocation', style={ 'textAlign': 'center', 'fontSize': 16, 'font-weight': 'bold', 'font-family': 'arial'},
                            className="gs-header gs-text-header padded"),
                    dcc.Graph(
                        id = "graph-1",
                        figure={
                            'data': [
                           go.Pie(labels=assets, values=proportions,
                               hoverinfo='label+percent', 
                               textinfo='label+percent', 
                               textfont=dict(size=14),
                               marker=dict(colors=colors, line=dict(color='#000000', width=2)),
                               textposition ='outside',
                               showlegend=False)

                            ],
                            'layout': go.Layout(
                                autosize = False,
                                bargap = 0.35,
                                font = {
                                  "family": "Raleway",
                                  "size": 10
                                },
                                height = 400,
                                hovermode = "closest",

                                margin = {
                                  "r": 25,
                                  "t": 125,
                                  "b": 80,
                                  "l": 52,
                                  "pad":0
                                },
                                showlegend = True,
                                title = "",
                                width = 340,

                            ), 
                        },
                        config={
                            'displayModeBar': False
                        }
                    )
                ], className="six columns"),

                html.Div([
                    html.H6("Hypothetical growth of $1,000 over a year", style={ 'textAlign': 'center', 'fontSize': 16, 'font-weight': 'bold', 'font-family': 'arial'},
                            className="gs-header gs-table-header padded"),
                    dcc.Graph(
                        id="graph-2",
                        figure={
                                'data': [
                                    {'x': investment_data['Date'], 'y': investment_data['SmartPortfolio'], 'type': 'scatter', 'name': 'Smart Crypto Index'},
                                    {'x': investment_data['Date'], 'y': investment_data['Top15Weighted'], 'type': 'scatter', 'name': 'Top 15 Weighted'},
                                    {'x': investment_data['Date'], 'y': investment_data['CoinBase'], 'type': 'scatter', 'name': 'Coinbase Index'}
                    
                                ],

                            'layout': go.Layout(
                                autosize = False,
                                title = "",
                                font = {
                                  "family": "arial",
                                  "size": 12
                                },
                                height = 350,
                                width = 340,
                                hovermode = "closest",
                                legend = {
                                  "x": -0.0277108433735,
                                  "y": -0.3,
                                  "orientation": "h"
                                },
                                margin = {
                                  "r": 10,
                                  "t": 20,
                                  "b": 20,
                                  "l": 50
                                },
                                showlegend = True,
                                xaxis=dict(
                                    titlefont=dict(
                                        family='Arial',
                                        size=14
                                    ),
                                    showticklabels=True,
                                    tickangle=-45,
                                    tickfont=dict(
                                        family='arial',
                                        size=14,
                                        color='black'
                                    )
                                    ),
                                    yaxis=dict(
                                        title='Investment Worth ($USD)',
                                        titlefont=dict(
                                            family='Arial',
                                            size=14

                                        ),
                                        showticklabels=True,

                                        tickfont=dict(
                                            family='arial',
                                            size=14
                                        )
                            ))
                        },
                        config={
                            'displayModeBar': False
                        }
                    )
                ], className="six columns"),

            ], className="row "),



        ], className="subpage")

    ], className="page")



# Describe the layout, or the UI, of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Update page
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == '/overview':
        return overview
    


external_css = ["https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
                "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "//fonts.googleapis.com/css?family=Raleway:400,300,600",
                'https://codepen.io/ctraverse/pen/oabgKM.css',
                "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ["https://code.jquery.com/jquery-3.2.1.min.js",
               "https://codepen.io/plotly/pen/KmyPZr.js"]

for js in external_js:
    app.scripts.append_script({"external_url": js})

if __name__ == '__main__':
    app.run_server(debug=True,port=5000,host='0.0.0.0')
