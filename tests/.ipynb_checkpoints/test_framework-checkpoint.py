import unittest


from src.read_write import ReadData
from src.utils import daterange
from src.stock import Stock, Holding, Universe
from src.strategy import StupidStrategy, BenchMarkStrategy, RandomStrategy
from src.backtest import BackTest
from src.linreg_strategy import LinRegStrategy
from src.factor import Factor, LinRegFactor, MovingAverageFactor



# write all the tests
class TestFrameWork(unittest.TestCase):
    def test_read_data(self):
        read_data = ReadData('AAPL')
        read_df = read_data.get_data(start_date='2019-12-01', end_date='2019-12-07', 
                                     online=True)
        self.assertTrue(read_df.shape[0] > 0)
        
        read_df_2 = read_data.get_data(start_date='2019-12-01', end_date='2019-12-07', 
                                     online=False)
        self.assertTrue(read_df_2.shape[0] > 0)
    
    def test_daterange(self):
        for d in daterange('2019-12-02', '2019-12-04'):
            print(d)

    def test_stock(self):
        test_stock = Stock('AAPL')
        test_price = test_stock.get_price('2019-12-02')
        test_price_df = test_stock.get_price_history(
            start_date='2019-12-01', end_date='2019-12-09')
        # buy 10, sell 9, check if it is still held
        test_stock.buy(date='2019-12-02', num=10)
        test_stock.sell(date='2019-12-03', num=9)
        self.assertEqual(test_stock.is_held(), True)
        # sell the remaining one and check not held
        test_stock.sell(date='2019-12-03', num=1)
        self.assertEqual(test_stock.is_held(), False)
    
    def test_holding(self):
        test_holding = Holding(cash=100000.)
        stock_1 = Stock('AAPL')
        test_holding.record(date='2019-12-02', symbol='AAPL', 
                            num=10, record_type='buy')
        
        test_holding.record(date='2019-12-02', symbol='AMZN', 
                            num=10, record_type='buy')
        
        test_holding.record(date='2019-12-02', symbol='AMZN', 
                            num=10, record_type='sell')
    
    def test_universe(self):
        test_universe = Universe()
        test_universe.add('AAPL')
        test_universe.add('AMZN')
        test_universe.add('ADBE')
        all_stocks = test_universe.get_universe()

        self.assertEqual(set(all_stocks), {'AAPL','AMZN','ADBE'})
    
    def test_strategy(self):
        test_universe = Universe()
        test_stocks = ['AAPL','AMZN','ADBE']
        for symbol in test_stocks:
            test_universe.add(symbol)
        
        test_strategy = StupidStrategy(universe=test_universe, 
                                       start_str='2019-12-02',
                                       end_str='2019-12-05',
                                       cash=100000)
        
        test_strategy.play('2019-12-02')
    
    def test_benchmark_strategy(self):
        test_universe = Universe()
        test_universe.add('VOO')

        bench_strategy = BenchMarkStrategy(
            universe=test_universe, 
            start_str='2019-12-02',
            end_str='2019-12-05',
            cash=10000)


        bench_strategy.play('2019-12-02')
        bench_strategy.play('2019-12-03')

    def test_backtest(self):
        test_universe = Universe()
        test_stocks = ['AAPL','AMZN','ADBE']
        for symbol in test_stocks:
            test_universe.add(symbol)
        
        test_strategy = StupidStrategy(universe=test_universe, 
                                       start_str='2019-12-01',
                                       end_str='2019-12-10',
                                       cash=100000)
        
        test_backtest = BackTest(this_strategy=test_strategy, start_date
                                 ='2019-12-01', end_date='2019-12-04')
        test_backtest.play_backtest(visualize=False)
        
    def test_random_strategy(self):
        test_universe = Universe()
        all_stocks = [
            'NOK', 'UAL', 'IAG', 'CPE', 
            'SWN','ITP','AREC',  'DCIX', 'SDPI' 
        ]

        for symbol in all_stocks:
            test_universe.add(symbol)

        test_strategy = RandomStrategy(universe=test_universe, 
                                        start_str='2019-12-01',
                                        end_str='2019-12-15',
                                        cash=10000)

        test_backtest = BackTest(this_strategy=test_strategy, 
                                 start_date='2019-12-01', 
                                 end_date='2019-12-15')
        
        test_backtest.play_backtest(visualize=False)
    
    def test_linreg_strategy(self):
        test_universe = Universe()
        test_stocks = ['AAPL','AMZN','ADBE', 'SWN','VOO', 'VCR']
        for symbol in test_stocks:
            test_universe.add(symbol)
        
        test_strategy = LinRegStrategy(universe=test_universe, 
                                       start_str='2019-12-01',
                                       end_str='2019-12-20',
                                       cash=100000)
        
        test_backtest = BackTest(this_strategy=test_strategy, start_date
                                 ='2019-12-01', end_date='2019-12-20')
        test_backtest.play_backtest(visualize=False)
        
    def test_linreg_factor(self):
        test_stock = Stock('AAPL')
        linreg = LinRegFactor(num_days=30)
        beta = linreg(stock=test_stock,end_date='2019-11-15')
        
    def test_ma_factor(self):
        test_stock = Stock('AAPL')
        ma_fac = MovingAverageFactor(short_term=20, long_term=100)
        ma_1 = ma_fac(stock=test_stock,end_date='2019-11-15')
        
        