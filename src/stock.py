import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple 
import logging

from .read_write import ReadData, check_valid_symbol
from .utils import date_n_day_from

#save logging
logging.basicConfig(filename='log.txt', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)


class Transaction(object):
    def __init__(self, num: int, price: float, date : str, buy_or_sell: str):
        self.num = num
        self.price = price
        self.date= date
        self.buy_or_sell = buy_or_sell
        if self.buy_or_sell not in ['buy', 'sell']:
            raise ValueError(f'buy_or_sell is {self.buy_or_sell}') 
    

class Stock(object):
    """
    Defines an individual stock.
    This object contains the state of the stock
    """
    def __init__(self, stock_symbol: str, verbose: bool = True):
        self.stock_symbol = stock_symbol
        self.transaction_list = []
        self.total_num = 0
    
        self.current_hold = False
        self.verbose = verbose

        self.read_data = ReadData(stock_symbol)

        #keep accounts
        self.total_buy_cost = 0. # how much did you pay to buy these stocks
        self.total_sales = 0. # how much did you make selling these stocks
        self.current_valuation = 0. # what is the current value of this stock
                                    # holding today?
    
    def get_symbol(self):
        return self.stock_symbol
    
    def get_total_buy_cost(self):
        return self.total_buy_cost

    def get_price(self, date: str, is_strict: bool = False) -> float:
        # We take the price to the be the opening price.
        # Should we change it?
        # Sometimes some stock might miss price data for a day
        # if you are trying to buy or sell, this should raise an
        # error. If you are simply trying to do some accounting,
        # we will give you a best possible price, just so not to raise 
        # an error


        
        read_df = self.read_data.get_data(
            start_date=date, end_date=date)
        #counter = 0
        #if read_df.shape[0] == 0:
        #    while(read_df.shape[0] == 0 and counter < 5):
        #        read_df = self.read_data.get_data(
        #            start_date=date, end_date=date)
        #        counter += 1

        if read_df.shape[0] != 1:
            if is_strict:
                raise ValueError(f"""
                    We expected 1 row, but got {read_df.shape[0]}
                    Cannot retrieve price for {self.stock_symbol} for 
                    {date}. If you can live with non-exactness, call 
                    the get_price() function with non_strict=False
                """)
            else:
                start_date = date_n_day_from(date=date, delta=-7)
                end_date = date_n_day_from(date=date, delta=7)
                read_df = self.read_data.get_data(
                    start_date=start_date, end_date=end_date)
                if read_df.shape[0] == 0:
                    raise ValueError(f"""
                        Stock price does not exist for 14 days for 
                        {self.stock_symbol} from {start_date} to {end_date},
                        Hence, get_price() fails even in non-strict mode)
                        """
                    )


        return read_df['Open'][0]
    
    def get_price_history(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        returns the history of the price from the start day to the end day
        """
        read_df = self.read_data.get_data(
                    start_date=start_date, end_date=end_date)
    
        read_df_select = read_df[['Open']]

        return read_df_select

    def buy(self, date: str, num: int):
        this_transaction = Transaction(
            num=num,
            price=self.get_price(date),
            date=date,
            buy_or_sell='buy'
        )

        self._record_transaction(this_transaction)
    
    def sell(self, date: str, num: int):
        # todo prevent from selling if we don't have enough
        this_transaction = Transaction(
            num=num,
            price=self.get_price(date),
            date=date,
            buy_or_sell='sell'
        )
        
        self._record_transaction(this_transaction)
        
    def _record_transaction(self, t: Transaction):
        if t.buy_or_sell == 'sell':
            if t.num > self.total_num:
                raise ValueError(
                    f"""
                    Cannot sell {t.num} stocks, 
                    you only hold {self.total_num} stocks of 
                    {self.stock_symbol}
                    """
                )
        
        if t.buy_or_sell == 'sell':
            self.total_num -= t.num 
            self.total_sales += t.num * t.price

            if self.total_num == 0:
                self.current_hold = False
        
        elif t.buy_or_sell == 'buy':
            self.total_num += t.num 
            self.total_buy_cost += t.num * t.price
            self.current_hold = True 
        else:
            raise ValueError(f'Should be buy or sell, it is {t.buy_or_sell}')

        self.transaction_list.append(t)
        self._update_current_valuation(t.date)
        #if self.verbose:
        self._log_info(t)

    def is_held(self) -> bool:
        return self.current_hold
    
    def _log_info(self, t: Transaction):
        """
        Logs info on a transaction
        """
        # for now use print, can move to logger later
        log.info(f"Date: {t.date}")
        log.info(f"Stock symbol: {self.stock_symbol}")
        log.info(f"Action: {t.buy_or_sell}")
        log.info(f"Price: {t.price}")
        log.info(f"Number of Stocks: {t.num}")

        log.info(f"Number of stocks held: {self.total_num}")
        log.info(f"Value of stocks held: {self.current_valuation}")
    
    def get_valuation(self, date: str, is_strict: bool = True) -> float:
        if is_strict:
            self._update_current_valuation(date)
        else:
            try:
                self._update_current_valuation(date) 
            except:
                pass
        return self.current_valuation
    
    def _update_current_valuation(self, date: str):
        self.current_valuation = self.total_num * self.get_price(date)
        


        
        
class Holding(object):
    """
    This class defines the current holdings, and also keeps track of 
    all the statistics corresponding to it, such as returns etc. At a given time
    this can be called to tell us the current returns, current holdings etc.
    """

    def __init__(self, cash: float):
        self.all_stocks = [] 
        self.cash = cash
        self.starting_cash = cash
        self.accounts = {
            'amount_invested': cash,
            'current_valuation': cash,
            'total_profit': 0.,
            'cash_in_hand': cash,
            'stocks_held': []
        }

    
    def record(self, date: str, symbol: str, num: int, record_type: str,
               verbose: bool = True):
        """
        Updates the holding when a transaction happens.
        This searches the current holding to check if the stock exists and 
        updates its state. Otherwise, it creates a new stock
        """
        if record_type not in ['buy', 'sell']:
            raise ValueError(
                f"record type should be buy or sell, it is {record_type}")

        # if stock not in portfolio, add it
        if self._get_stock(symbol) is None:
            new_stock = Stock(stock_symbol = symbol,verbose=verbose)
            self.all_stocks.append(new_stock)
        
        this_stock = self._get_stock(symbol)
       
        
        if record_type == 'buy':
            if self._has_cash(this_stock=this_stock, date=date, num=num):
                this_stock.buy(date=date, num=num)
        else:
            this_stock.sell(date=date, num=num)

        self._update_cash(this_stock=this_stock, date=date, num=num,
                          record_type=record_type)
    
    def _get_stock(self, symbol: str):
        for stock in self.all_stocks:
            if stock.stock_symbol == symbol:
                return stock
        
        return None

    def _has_cash(self, this_stock: Stock, date: str, num: int):
        """
        queries if there is enough cash to buy this stock
        """
        amount = this_stock.get_price(date) * num 
        if (self.cash - amount) < 0.:
            return False
        else:
            return True

    def _update_cash(self, this_stock: Stock, date: str, num: int,
                         record_type: str):
        """
        Updates the books, after each transaction
        """ 
        if record_type not in ['buy', 'sell']:
            raise ValueError(
                f"record type should be buy or sell, it is {record_type}")
            
        amount = this_stock.get_price(date) * num 

        if record_type == 'buy':
            if (self.cash - amount) < 0.:
                raise ValueError(
                    f"""
                    You are trying to buy {amount} but you only have {self.cash}.
                    Your order is for {num} of {this_stock.stock_symbol}, 
                    which costs {num} X {this_stock.get_price(date)} = {amount}
                    """
                )
            self.cash -= amount
        else:
            self.cash += amount

    def get_cash(self) -> float:
        return self.cash

    def get_holding_info(self, date: str, is_strict: bool = True):
        """
        What is the current state of the account?
        """
        # optimize this later, you don't need to go through all stocks to 
        # calculate valuation
        self.accounts['cash_in_hand'] = self.cash
        self.accounts['current_valuation'] = sum(
            [x.get_valuation(date, is_strict) for x in self.all_stocks]
        ) + self.cash
        self.accounts['total_profit'] = (
            self.accounts['current_valuation'] -   
            self.accounts['amount_invested']
        )
        self.accounts['stocks_held'] = ([
            x.stock_symbol for x in self.all_stocks if x.is_held()])

        return self.accounts

class Account(object):
    """
    Contains all the accouting for a holding
    """
    def __init__(self, holding: Holding):
        self.holding = holding
        self.amount_invested = self.holding.get_cash()
        self.current_valuation = self.holding.get_cash()
        self.total_profit = 0.
        self.cash_in_hand = self.holding.get_cash()
        self.stocks_held = []

    def __str__(self):
        class_str = ','.join([
            'amount_invested: ', str(self.amount_invested),
            'current_valuation: ', str(self.current_valuation),
            'total_profit: ', str(self.total_profit),
            'cash_in_hand: ', str(self.cash_in_hand),
            'stocks_held: ', str(self.stocks_held)
        ])
        
        return class_str
    
    def update_holding_info(self, date: str,is_strict: bool = True):
        self.cash_in_hand = self.holding.get_cash()
        self.current_valuation = sum(
            [x.get_valuation(date,is_strict) for x in self.holding.all_stocks]
        ) + self.holding.get_cash()

        self.total_profit = (self.current_valuation - self.amount_invested)

        self.stocks_held = ([
            x.stock_symbol for x in self.holding.all_stocks if x.is_held()])
    


class Universe(object):
    """
    This defines an universe of stocks, from which one can choose stocks.
    """
    def __init__(self):
        self.all_symbols = []
    
    def add(self, symbol: str):
        if not check_valid_symbol(symbol):
            raise ValueError(f'Cannot add {symbol}')
        
        if symbol not in self.all_symbols:
            self.all_symbols.append(symbol)
    
    def get_universe(self) -> List[str]:
        return self.all_symbols
    
    

    