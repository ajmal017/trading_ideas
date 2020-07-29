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
        # TODO define a queue for FIFO 
        # keep track of realized and unrealized profits
        
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
        """
        returns the amount spent to buy this stock, over time
        """
        return self.total_buy_cost
    
    def get_total_sell_cost(self):
        """
        returns the "realized" amount, by selling this stock.
        """
        return self.total_sales

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


        return read_df['Open'].values[0]
    
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
        

class Account(object):
    """
    Contains all the accounting for a holding
    """
    def __init__(self, 
                 amount_invested: float = 0., 
                 current_valuation: float = 0.,
                 total_profit: float = 0.,
                 cash_in_hand: float= 0.,
                 stocks_held: List[Stock]= []):
        #TODO need to add realized profit in addition to total profit
        # realized profit needs to be added to the stock class as well
        
        self.amount_invested = amount_invested
        self.current_valuation = current_valuation
        self.total_profit = total_profit
        self.cash_in_hand = cash_in_hand
        self.stocks_held = stocks_held

    def __str__(self):
        class_str = ','.join([
            'amount_invested: ', str(self.amount_invested),
            'current_valuation: ', str(self.current_valuation),
            'total_profit: ', str(self.total_profit),
            'cash_in_hand: ', str(self.cash_in_hand),
            'stocks_held: ', ','.join([x.get_symbol() for x in self.stocks_held])
        ])
        
        return class_str
    
    def update_account(self, this_stock: Stock, date: str, num: int,
                       record_type: str):
        if record_type not in ['buy', 'sell']:
            raise ValueError(
                f"record type should be buy or sell, it is {record_type}"
            )
            
        self.update_cash(this_stock=this_stock, date=date, num=num,
                    record_type=record_type)
    
        self.update_holding_info(date)
        
    
    def update_holding_info(self, date: str,is_strict: bool = True):
        
        self.update_stocks()
        
        self.current_valuation = sum(
            [x.get_valuation(date,is_strict) for x in self.stocks_held]
        ) + self.cash_in_hand

        self.total_profit = (self.current_valuation - self.amount_invested)
        

        
    def update_stocks(self):
        """
        Updates which stocks are currently held.
        """
        self.stocks_held = [x for x in self.stocks_held if x.is_held()]
    
    def get_stock(self, symbol: str):
        """
        returns a stock if its available, else returns none
        """
        for stock in self.stocks_held:
            if stock.stock_symbol == symbol:
                return stock
        
        return None 
    
    def add_and_get_stock(self, symbol: str, verbose: bool):
        """
        returns a stock if its not available, else adds it and 
        returns the added stock
        """
        if self.get_stock(symbol) is None:
            new_stock = Stock(stock_symbol = symbol,verbose=verbose)
            self.stocks_held.append(new_stock)
            return new_stock
        else:
            return self.get_stock(symbol)
        
    def get_cash(self) -> float:
        return self.cash_in_hand
    
    def get_stock_symbols(self) -> List[str]:
        self.update_stocks()
        
        return [x.get_symbol() for x in self.stocks_held]
    
        
    
    def update_cash(self, this_stock: Stock, date: str, num: int,
                    record_type: str):
        """
        Updates the books, after each transaction
        """ 
        
        if record_type not in ['buy', 'sell']:
            raise ValueError(
                f"record type should be buy or sell, it is {record_type}")
            
        amount = this_stock.get_price(date) * num 

        if record_type == 'buy':
            if (self.cash_in_hand - amount) < 0.:
                raise ValueError(
                    f"""
                    You are trying to buy {amount} but you only have {self.cash_in_hand}.
                    Your order is for {num} of {this_stock.stock_symbol}, 
                    which costs {num} X {this_stock.get_price(date)} = {amount}
                    """
                )
            self.cash_in_hand -= amount
        else:
            self.cash_in_hand += amount
    
    def has_cash(self, this_stock: Stock, date: str, num: int):
        """
        queries if there is enough cash to buy this stock
        """
        amount = this_stock.get_price(date) * num 
        if (self.cash_in_hand - amount) < 0.:
            return False
        else:
            return True
        
        
    


        
class Holding(object):
    """
    This class defines the current holdings, and also keeps track of 
    all the statistics corresponding to it, such as returns etc. At a given time
    this can be called to tell us the current returns, current holdings etc.
    """
    #TODO add methods to add/substract cash

    def __init__(self, cash: float):
        self.all_stocks = [] 
        self.cash = cash
        self.starting_cash = cash
        self.account = Account(
            amount_invested = cash,
            current_valuation = cash,
            total_profit = 0.,
            cash_in_hand = cash,
            stocks_held = []
        )

    
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

        
        this_stock = self.account.add_and_get_stock(symbol, verbose)

        
        if record_type == 'buy':
            if self.account.has_cash(this_stock=this_stock, date=date, num=num):
                this_stock.buy(date=date, num=num)
                
                self.account.update_account(this_stock=this_stock, date=date, 
                                            num=num, record_type=record_type)
            else:
                print(f"""
                Tried to buy {num} shares of {this_stock.symbol} but
                dont have enough cash
                """)
        else:
            this_stock.sell(date=date, num=num)

            self.account.update_account(this_stock=this_stock, date=date, 
                                        num=num, record_type=record_type)
                

    def get_cash(self) -> float:
        return self.account.get_cash()

    def get_holding_info(self, date: str, is_strict: bool = True):
        """
        What is the current state of the account?
        Refresh the valuation for the current date
        """
        self.account.update_holding_info(date, is_strict)
        return self.account
    
    def get_stocks_held(self) -> List[str]:
        """
        returns the list of current stocks held.
        """
        # TODO should we return the symbols?
        # it is potentially unsafe that the caller can modify the Stock objects
        
        
        return self.account.get_stock_symbols()


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
    
    

    