from pandas_datareader import data as pdr
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

yf.pdr_override() 

class ReadData(object):
    """
    This class provides all the necessary abstraction to read data.
    It abstracts how the data is stored, how calls are made etc.
    It provides the interface to read the data for a given stock
    """
    def __init__(self, stock_symbol: str):
        self.stock_symbol = stock_symbol

    def get_data(self, start_date: str, end_date: str,
                 online: bool=True) -> pd.DataFrame:
        if online:
            panel_data = self._get_data_online(start_date, end_date)
        else:
            panel_data = self._get_data_offline(start_date, end_date)

        return panel_data 
    
    def _get_data_online(self, start_date: str, end_date:str) -> pd.DataFrame:
        try:
            #panel_data = pdr.DataReader(self.stock_symbol, 'yahoo', 
            #                             start_date, end_date)
            panel_data = pdr.get_data_yahoo(self.stock_symbol, start_date, end_date)
        except:
            print(f"""
            Could not find symbol for {self.stock_symbol} for dates {start_date}
            and {end_date}
            """)
            
            panel_data = pd.DataFrame(
                columns=['High','Low','Open','Close', 'Volume', 'Adj Close'])
            
        
        return panel_data

    def _get_data_offline(self, start_date: str, end_date:str) -> pd.DataFrame:
        offline_filename = '/home/souravc83/trading_ideas/src/data/offline_price_data.csv'
        all_df = pd.read_csv(offline_filename)
        all_df['date'] = pd.to_datetime(all_df['date'])
        filt_df = all_df.query(f"symbol=='{self.stock_symbol}'")
        
        start_date_dt =  datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt =  datetime.strptime(end_date, '%Y-%m-%d')
        
        panel_data = filt_df[
            (filt_df['date']>= start_date_dt) & (filt_df['date']<= end_date_dt)
        ]
        
        return panel_data

    
class WriteData(object):
    """
    This is run periodically, in order to write the data corresponding to
    each stock. Ideally, we want to save the data locally, so that we 
    don't have to make a network call every time we want the data.
    We want to update the saving every time we run this to pull in fresh data
    """
    def __init__(self):
        pass

def check_valid_symbol(symbol: str) -> bool:
    """
    quickly check if a stock symbol is available
    should have 5 days of data between 12-02 and 12-06
    """
    read_data = ReadData(symbol)
    read_df = read_data.get_data(start_date='2019-12-02', end_date='2019-12-06')
    if read_df.shape[0] == 4:
        return True 
    else:
        return False

    
# one time scripts we ran
def collect_valid_sp500():
    sp_500_filename = '/home/souravc83/trading_ideas/src/data/sp500.csv'
    valid_sp_500_filename = '/home/souravc83/trading_ideas/src/data/sp500_valid.csv'
    df = pd.read_csv(sp_500_filename)
    
    df['is_valid'] = df.Symbol.apply(check_valid_symbol)
    df_filtered = df.query('is_valid == True')
    df_filtered.columns = ['symbol', 'name', 'sector', 'is_valid']
    df_filtered = df_filtered[['symbol', 'name', 'sector']]
    df_filtered.to_csv(path_or_buf=valid_sp_500_filename, index=False, header=True)
    
    
def prep_df_join(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    df['symbol'] = symbol
    df['date'] = df.index
    return df

def make_big_dataframe(symbol_list, start_date='2019-12-02', end_date='2019-12-06'):
    df_list = []
    for symbol in symbol_list:
        try:
            A = ReadData(symbol)
            df = A.get_data(start_date=start_date, end_date=end_date)
            df = prep_df_join(df, symbol)
            #print(df)
            df_list.append(df)
        except:
            pass
    #print(df_list)
    big_df = pd.concat(df_list, ignore_index=True)
    return big_df

def store_all_data(start_date: str = '2015-01-02' , end_date: str = '2020-06-21'):
    valid_sp_500_filename = '/home/souravc83/trading_ideas/src/data/sp500_valid.csv'
    offline_filename = '/home/souravc83/trading_ideas/src/data/offline_price_data.csv'
    df = pd.read_csv(valid_sp_500_filename)
    symbol_list = list(df['symbol'].values)
    
    big_df = make_big_dataframe(symbol_list, start_date, end_date)
    big_df.to_csv(path_or_buf=offline_filename, index=False, header=True)
    
    