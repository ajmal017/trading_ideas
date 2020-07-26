"""
Declares factors. A factor is a class 
that takes a Stock and returns a float
"""
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List
from datetime import timedelta, date, datetime
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None 

from .stock import Stock
from .utils import date_n_day_from

class Factor(object):
    """
    Abstract class that defines a factor
    """
    def __init__(self):
        self.value = np.nan
    
    def __call__(self, stock: Stock, end_date: str, **kwargs):
        self.stock = stock
        self.end_date = end_date
        
        self._calc_factor(**kwargs)
        return self.value
    
    def _calc_factor(self, **kwargs):
        raise NotImplementedError("Subclasses should implement")
        
        
def linreg_stock(stock_ticker='AAPL', start_date = '2019-12-01',
                 end_date = '2020-02-05', visualize=False):
    """
    Defines an ordinary linear regression, between time and 
    stock price. The function returns the 95% confidence interval
    of the slope beta
    """
    this_stock = Stock(stock_ticker)
    panel_data = this_stock.get_price_history(
        start_date=start_date, end_date=end_date)
    if panel_data.shape[0] == 0:
        return [np.nan, np.nan]

    panel_data['x_val'] = list(range(panel_data.shape[0]))

    X = panel_data['x_val']
    y = panel_data['Open'].values/panel_data['Open'].values[0]
    X = sm.add_constant(X)
    model = sm.OLS(y, X)
    results = model.fit()

    A = results.conf_int(alpha=0.05, cols=None)

    beta_lower = A[0]['x_val']
    beta_upper = A[1]['x_val']

    if visualize:
        prstd, iv_l, iv_u = wls_prediction_std(results)

        plt.plot(panel_data['x_val'], y, 'ro')
        plt.plot(panel_data['x_val'], results.fittedvalues, 'r--.', label="OLS")

        plt.plot(panel_data['x_val'], iv_l, 'b--.')
        plt.plot(panel_data['x_val'], iv_u, 'b--.')
    return [beta_lower, beta_upper]

        
class LinRegFactor(Factor):
    """
    This returns the mean of the slope of the linear regression
    """
    def __init__(self, num_days: int = 30):
        Factor.__init__(self)
        self.num_days = num_days
    
    def _calc_factor(self):
        """
        overrides the parent class.
        Args:
            end_date: str the end date
            num_days: int number of days before to start
        """
        stock_symbol = self.stock.get_symbol()
        
        start_date = date_n_day_from(date=self.end_date, 
                                     delta=(-1)* self.num_days)
        beta_list = linreg_stock(
            stock_ticker=stock_symbol, start_date=start_date, 
            end_date=self.end_date, visualize=False)
        if not np.isnan(beta_list[0]):
            beta_mean = 0.5 * (beta_list[0] + beta_list[1])
        else:
            beta_mean = 0.
            
        self.value = beta_mean
        
class MovingAverageFactor(Factor):
    def __init__(self, short_term : int = 20, long_term : int = 100):
        Factor.__init__(self)
        
        self.short_term = short_term
        self.long_term = long_term
    
    def _calc_factor(self):
        
        short_start_date = date_n_day_from(
            date=self.end_date, delta=(-1)*self.short_term)
        long_start_date = date_n_day_from(
            date=self.end_date, delta=(-1)*self.long_term)
        
        short_data = self.stock.get_price_history(
            start_date=short_start_date, end_date=self.end_date
        )
        
        long_data = self.stock.get_price_history(
            start_date=long_start_date, end_date=self.end_date
        )
        
        short_ma = np.mean(short_data['Open'].values)
        long_ma = np.mean(long_data['Open'].values)
        
        self.value = short_ma/long_ma

class PercReturnFactor(Factor):
    """
    Percentage Return in N days
    """
    def __init__(self,n_day: int = 7):
        Factor.__init__(self)
        self.n_day = n_day
    
    def _calc_factor(self):
        
        start_date = date_n_day_from(
            date=self.end_date, delta=(-1)*self.n_day
        )
        
        all_data = self.stock.get_price_history(
            start_date=start_date, end_date=self.end_date
        )
        
        df_size = all_data.shape[0]
        
        n_day_return = all_data['Open'].values[df_size - 1]/all_data['Open'].values[0]
        
        self.value = n_day_return


        
    

