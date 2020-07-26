from .strategy import Strategy, BenchMarkStrategy
from .utils import daterange, is_weekday
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import timedelta, date, datetime



class BackTest(object):
    """
    This class performs a backtest, given a strategy, date etc. and returns 
    metrics corresponding to the backtest
    """

    def __init__(self, this_strategy: Strategy, 
                 start_date: str, end_date: str, verbose: bool = True):
        self.strategy = this_strategy
        self.start_date = start_date
        self.end_date = end_date
        self.verbose = verbose

        self.benchmark_strategy = BenchMarkStrategy(
            universe=this_strategy.universe, start_str=this_strategy.start_str,
            end_str=this_strategy.end_str, cash= this_strategy.init_cash,
            verbose=self.verbose
        )

    def play_backtest(self, visualize: bool = True):
        """
        Run the backtest every day
        """
        date_list = []
        total_value = []
        total_profit = []
        #sp benchmark to be added
        benchmark_value = []
        benchmark_profit = []


        for d in daterange(start_date=self.start_date, end_date=self.end_date):
            if is_weekday(d):
                print(f"Executing {d}")
                
                account = self.strategy.play(d)
                benchmark_account = self.benchmark_strategy.play(d)

                date_list.append(datetime.strptime(d, '%Y-%m-%d'))

                total_value.append(account.current_valuation)
                benchmark_value.append(benchmark_account.current_valuation)

                total_profit.append(account.total_profit)
                benchmark_profit.append(benchmark_account.total_profit)
        
        if visualize:
            sns.set()
            fig1, ax1 = plt.subplots()
            ax1.plot(date_list, total_value, 'bo')
            ax1.plot(date_list, benchmark_value, 'ko-')
            ax1.set_ylabel('Total Value')
            labels = ax1.get_xticklabels()
            plt.setp(labels, rotation=45, horizontalalignment='right')

            fig2, ax2 = plt.subplots()
            ax2.plot(date_list, total_profit, 'ro')
            ax2.plot(date_list, benchmark_profit, 'ko-')
            ax2.set_ylabel('Total Profit')
            labels = ax2.get_xticklabels()
            plt.setp(labels, rotation=45, horizontalalignment='right')