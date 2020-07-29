import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

from .stock import Universe, Account, Holding, Stock
from .utils import is_weekday

import logging


#save logging
logging.basicConfig(filename='log.txt', filemode='w', level=logging.INFO)
log = logging.getLogger(__name__)


class StockChoice(object):
    """
    A stock chosen by the strategy class.
    This defines the information about the stock,
    including the symbol, number of stocks, 
    is the reco to buy or sell
    """

    def __init__(self, symbol: str, num: int, reco: str):
        self.symbol = symbol
        self.num = num
        if reco not in ['buy', 'sell', 'hold']:
            raise ValueError(f'reco is {reco}, should be buy/sell/hold')    
        self.reco = reco


class Strategy(object):
    """
    This class defines a trading strategy. Given an universe, holding, date, 
    the total cash you are starting with etc. 
    this class can be called to advice what to buy/sell on a given date
    """

    def __init__(self, universe: Universe, start_str: str, end_str: str, 
                 cash: float, verbose: bool = True):
        self.start_str = start_str
        self.end_str = end_str
        self.universe = universe
        self.holding = Holding(cash=cash)
        self.init_cash = cash
        self.verbose = verbose

    def play(self, date_today : str):
        """
        Given a day, this is going to be a playing strategy.
        Implemented by classes inheriting from here
        """
        # day should be weekday
        if not is_weekday(date_today):
            raise ValueError(
                f'Should be called only on weekdays, called on {date_today}')
            
        # raise NotImplementedError("Subclasses should implement")
        stocks_list = self._choose_stocks(date_today)
        # reco can be 'buy', 'sell', 'hold'
        # todo holding class should implement buy and sell
        # not here
        for stock_choice in stocks_list:
            try:
                self.holding.record(date=date_today, 
                                    symbol=stock_choice.symbol, 
                                    num=stock_choice.num, 
                                    record_type=stock_choice.reco,
                                    verbose=self.verbose)
            except:
                print(f"""
                Could not execute order: {stock_choice.symbol},
                {stock_choice.num}, {stock_choice.reco}
                """)
                continue
        

        log.info(date_today)
        account = self.holding.get_holding_info(date_today)
        log.info(account)
        
        if self.verbose:
            print(date_today)
            print(account)

        return account
    
    def _choose_stocks(self, date: str) -> List[StockChoice]:
        raise NotImplementedError("Subclasses should implement")
        
        

# very simple strategy for illustration and testing
# buys a random stock every day
class StupidStrategy(Strategy):
    def __init__(self, universe: Universe, start_str: str, end_str: str,
                 cash: float, verbose: bool = True):
        Strategy.__init__(self,universe=universe, start_str=start_str, 
                          end_str=end_str, cash=cash, verbose=verbose)
        
    def _choose_stocks(self, date: str) -> List[StockChoice]:
        all_stocks = self.universe.get_universe()
        random_val = np.random.randint(low=0, high=len(all_stocks),size=1)[0]
        stock_chosen = all_stocks[random_val]
        stock_choice = StockChoice(symbol=stock_chosen, num=10, reco='buy')
        return [stock_choice]



class BenchMarkStrategy(Strategy):
    """
    This strategy buys VOO on the first day with all the money, and 
    then does nothing
    """        
    def __init__(self, universe: Universe, start_str: str, end_str: str,
                 cash: float, verbose: bool = True):
        Strategy.__init__(self,universe=universe, start_str=start_str, 
                          end_str=end_str, cash=cash, verbose=verbose)
        self.buy_flag = False
    
    def _choose_stocks(self, date: str) -> List[StockChoice]:
        if self.buy_flag:
            return []

        this_account = self.holding.get_holding_info(date=date, is_strict=True)
        etf_stock = Stock('VOO')
        stock_price = etf_stock.get_price(date)
        total_cash = self.holding.get_cash()
        num_etf_stock = int(np.floor(total_cash/stock_price))
        stock_chosen = StockChoice(symbol='VOO', num=num_etf_stock,
                                   reco='buy')
        self.buy_flag = True
        return [stock_chosen]

    
class RandomStrategy(Strategy):
    """
    Full Strategy, only stock picks are random
    every day, randomly decide to buy or sell
    every day, randomly find a stock to buy or sell
    if you don't have enough money to buy random stock
    or any stock to sell, pass

    This is a random strategy, but will force us to think 
    about all the practical aspects of building a strategy
    very simple strategy for illustration and testing
    buys a random stock every day
    """
    def __init__(self, universe: Universe, start_str: str, end_str: str,
                 cash: float, verbose: bool = True):
        Strategy.__init__(self,universe=universe, start_str=start_str, 
                          end_str=end_str, cash=cash, verbose=verbose)
        
    def _choose_stocks(self, date: str) -> List[StockChoice]:
        
        this_account = self.holding.get_holding_info(date=date, is_strict=True)
        all_stocks = self.universe.get_universe()

        # toss a coin and decide whether to buy or sell
        coin_toss = np.random.randint(low=0, high=2,size=1)[0]
        record_type = None
        if coin_toss == 0:
            record_type = 'buy'
        else:
            record_type = 'sell'
        
        if record_type == 'buy':
            # find a stock to buy
            all_stocks = self.universe.get_universe()
            rand_stock_num = np.random.randint(
                low=0, high=len(all_stocks),size=1)[0]
            

            stock_chosen = all_stocks[rand_stock_num]
            # can we buy this.
            try:
                this_stock = Stock(stock_chosen)
                stock_price = this_stock.get_price(date)
                if self.account.cash_in_hand > 10. * stock_price:
                    stock_choice = StockChoice(symbol=stock_chosen, num=10, 
                                           reco=record_type)
                    return [stock_choice]
            
                else:
                    return []
            except:
                return []
        else:
            stocks_held = self.holding.get_stocks_held()
            
            if len(stocks_held) == 0:
                return []
            else:
                rand_stock_num = np.random.randint(
                    low=0, high=len(stocks_held),size=1)[0]
                stock_chosen = stocks_held[rand_stock_num]
                # since its held, we definitely hold 10 of them
                # or more
                stock_choice = StockChoice(symbol=stock_chosen, num=10, 
                                           reco=record_type)

                return [stock_choice]
            