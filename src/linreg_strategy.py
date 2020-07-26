import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List
from datetime import timedelta, date, datetime
import numpy as np
import pandas as pd


from .stock import Stock, Holding, Account
from .strategy import Strategy, StockChoice
from .stock import Universe
from .utils import date_n_day_from
from .factor import LinRegFactor



class LinRegStrategy(Strategy):
     def __init__(self, universe: Universe, start_str: str, end_str: str,
                 cash: float, verbose: bool = True):
        Strategy.__init__(self,universe=universe, start_str=start_str, 
                          end_str=end_str, cash=cash, verbose=verbose)
        
        self.buy_flag = False
        self.sell_flag = False
        
     def _choose_stocks(self, date: str) -> List[StockChoice]:
        
        # rebalance every N days
        N_days = 3

        start_datetime = datetime.strptime(self.start_str, '%Y-%m-%d')
        now_datetime = datetime.strptime(date, '%Y-%m-%d')
        day_diff = int((now_datetime - start_datetime).days)

        if day_diff % N_days ==0 and self.sell_flag == False:
            self.sell_flag = True
            self.buy_flag = False

        basket = []
        
        linreg = LinRegFactor()

        if self.buy_flag:
            # Now buy back with new strategy
            all_stocks = self.universe.get_universe()

            
            symbol_dict = {}
            for stock_symbol in all_stocks:
                beta_mean = linreg(
                    stock=Stock(stock_symbol), 
                    end_date=date
                )
                
                symbol_dict[stock_symbol] = beta_mean
            
            min_beta = min(symbol_dict.values())
            symbol_dict_pos = {k: (v - min_beta) for k, v in symbol_dict.items()}

            cash_in_hand = self.holding.get_cash()
            #sum_beta = sum(symbol_dict_pos.values())
            #symbol_cash = {k: v*cash_in_hand/sum_beta for k, v in symbol_dict_pos.items()}

            #print(date)
            #print(symbol_dict)
            #print(symbol_cash)
            max_beta = max(symbol_dict.values())
            max_stock = None
            beta_now = min_beta
            for k, v in symbol_dict.items():
                if v > beta_now:
                    max_stock = k
                    beta_now = v

            this_stock = Stock(max_stock)
            stock_price = this_stock.get_price(date)
            num_stocks = int(np.floor(cash_in_hand/stock_price))
            stock_choice = StockChoice(symbol=max_stock, num=num_stocks, 
                                           reco='buy')
            basket.append(stock_choice)

            # once you have bought, set this to false 
            self.buy_flag = False





        if self.sell_flag:
            self.account.update_holding_info(date=date, is_strict=False)

            
            # First sell all the stocks that are making a profit, 
            # and then buy back rebalanced amounts
            # of the same stocks next day
            stocks_held = [x for x in self.holding.all_stocks if x.is_held()]
            for held_stock in stocks_held:
                current_val = held_stock.get_current_valuation()
                total_buy_cost = held_stock.get_total_buy_cost()
                
                if current_price/total_buy_cost > 1.05:
                    basket.append(
                        StockChoice(
                            symbol=held_stock.stock_symbol, 
                            num=held_stock.total_num,
                            reco='sell'
                        )
                    )
            self.sell_flag = False 
            self.buy_flag = True


        return basket