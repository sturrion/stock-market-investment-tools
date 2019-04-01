import pandas as pd
import numpy as np
import json
import requests

# Get Symbols
def get_df_symbols():
    # DOW Symbols
    dow_list = pd.read_csv('./data/dow.csv', sep=';')
    dow_list.set_index('Symbol', inplace=True)
    dow_list['DOW'] = True

    # S&P 500 Symbols
    sp_list = pd.read_csv('./data/sp500.csv', sep=';')
    sp_list.set_index('Symbol', inplace=True)
    sp_list['SP'] = True

    # NASDAQ 100 Symbols
    n100_list = pd.read_csv('./data/nasdaq100.csv', sep=',')
    n100_list.set_index('Symbol', inplace=True)
    n100_list['N100'] = True
    
    symbols_list = pd.merge(sp_list, dow_list, on='Symbol', how='outer')
    symbols_list = pd.merge(symbols_list, n100_list, on='Symbol', how='outer')
    
    symbols_list['DOW'] = np.where(symbols_list['DOW'].isna(), False, True)
    symbols_list['SP'] = np.where(symbols_list['SP'].isna(), False, True)
    symbols_list['N100'] = np.where(symbols_list['N100'].isna(), False, True)
    
    symbols_list['Company'] = np.where(symbols_list['DOW'] == True, 
                                       symbols_list['Company Name'], 
                                       np.where((symbols_list['DOW'] == False) & (symbols_list['SP'] == True), 
                                                symbols_list['Company_x'], 
                                                np.where((symbols_list['DOW'] == False) & (symbols_list['SP'] != True), 
                                                         symbols_list['Company_y'], ' ')))
        
    symbols_list = symbols_list[['Company', 'DOW', 'SP', 'N100']]
    
    return symbols_list

def get_companies_data(symbols_df):
    names = []
    exchanges = []
    industries = []
    sectors = []
    tags = []
    
    print('Get companies data')
    for index, row in symbols_df.iterrows():
        url = 'https://api.iextrading.com/1.0/stock/' + index + '/company'
        response = requests.get(url)
        info = json.loads(response.text)
        names.append(info['companyName'])
        exchanges.append(info['exchange'])
        industries.append(info['industry'])
        sectors.append(info['sector'])
        tags.append(info['tags'])
    
    symbols_df['Company Name'] = names
    symbols_df['Exchange'] = exchanges
    symbols_df['Industry'] = industries
    symbols_df['Sector'] = sectors
    symbols_df['Tags'] = tags
    
    return symbols_df

def get_stats_data(symbols_df):
    all_stats = pd.DataFrame() #creates a new dataframe that's empty
    
    print('Get stats')
    for index, row in symbols_df.iterrows():
        url = 'https://api.iextrading.com/1.0/stock/' + index + '/stats?displayPercent=true'
        response = requests.get(url)
        info = json.loads(response.text)

        df = pd.io.json.json_normalize(info)
        df['Symbol'] = index
    
        all_stats = all_stats.append(df, ignore_index = True) 

    all_stats.set_index('Symbol', inplace=True)
    symbols_list = pd.merge(symbols_df, all_stats, on='Symbol', how='left')
        
    return symbols_list

def get_prices(symbols_df):
    
    prices = []
    
    print('Prices')
    for index, row in symbols_df.iterrows():
        url = 'https://api.iextrading.com/1.0/stock/' + index + '/price'
        response = requests.get(url)
        prices.append(float(response.text))
        
    symbols_df['Price'] = prices
        
    return symbols_df
    
# To get all data from IEX
stocks_list = get_df_symbols()
stocks_list = get_companies_data(stocks_list.copy())
stocks_list = get_stats_data(stocks_list.copy())
stocks_list = get_prices(stocks_list.copy())
stocks_list.to_csv('./data/output/stocks.csv', sep=';')

writer = pd.ExcelWriter('./data/output/stocks.xlsx')
stocks_list.to_excel(writer,'Companies')
writer.save()

# Create a file with all_data for my portfolio symbols
portfolio = pd.read_csv('./data/symbols.csv')
portfolio.columns = ['Symbol']

df = pd.merge(stocks_list, portfolio, on='Symbol')
sorted_stocks = df.sort_values(by=['Sector', 'Industry', 'dividendYield'], ascending=[True, True, False])

writer = pd.ExcelWriter('./data/output/portfolio_stats.xls')
sorted_stocks.to_excel(writer)
writer.save()
