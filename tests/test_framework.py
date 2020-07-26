import unittest


from src.read_write import ReadData
from src.utils import daterange
from src.stock import Stock, Holding, Universe
from src.strategy import StupidStrategy, BenchMarkStrategy, RandomStrategy
from src.backtest import BackTest
from src.linreg_strategy import LinRegStrategy
from src.factor import Factor, LinRegFactor, MovingAverageFactor

# to run all tests:
# python3.8 -m unittest tests/test_framework.py

# to run a particular test:
# python3.8 -m unittest tests.test_framework.TestFrameWork.test_read_data

# write all the tests
class TestFrameWork(unittest.TestCase):
    def test_read_data(self):
        read_data = ReadData('AAPL')
        read_df = read_data.get_data(start_date='2019-12-02', end_date='2019-12-02', 
                                     online=True)
        self.assertTrue(read_df.shape[0] > 0)
        
        read_df_2 = read_data.get_data(start_date='2019-12-02', end_date='2019-12-02', 
                                     online=False)
        
        self.assertTrue(read_df_2.shape[0] > 0)
    
    def test_daterange(self):
        for d in daterange('2019-12-02', '2019-12-04'):
            print(d)

    def test_stock(self):
        # we will buy 10 stocks of apple on 2019-12-02
        # we will sell 1 stock on 2019-12-03
        # we will sell 9 stocks on 2019-12-09
        
        # Open prices
        # 2019-12-02: 267.269989
        # 2019-12-03: 258.309998
        # 2019-12-09: 270.000000
        
        test_stock = Stock('AAPL')
        self.assertEqual(test_stock.get_symbol(), 'AAPL')
        #get price
        test_price = test_stock.get_price('2019-12-02')
        self.assertAlmostEqual(test_price, 267.269989,places=2)
        
        # get price for a range
        test_price_df = test_stock.get_price_history(
            start_date='2019-12-01', end_date='2019-12-09')
        #market was open on 02,03,04,05,06,09:6 rows
        self.assertEqual(test_price_df.shape[0], 6)
        
        # buy 10
        test_stock.buy(date='2019-12-02', num=10)
        self.assertAlmostEqual(
            test_stock.get_total_buy_cost(),2672.69989, places=2
        )
        self.assertAlmostEqual(
            test_stock.get_total_sell_cost(),0., places=2
        )
        
        # sell 1
        test_stock.sell(date='2019-12-03', num=1)
        self.assertEqual(test_stock.is_held(), True)
        
        self.assertAlmostEqual(
            test_stock.get_total_buy_cost(),2672.69989, places=2
        )
        self.assertAlmostEqual(
            test_stock.get_total_sell_cost(),258.309998, places=2
        )
        
        # 258.309998 * 9
        self.assertAlmostEqual(
            test_stock.get_valuation('2019-12-03'), 2324.7899820000002, places=2
        )
        
        # sell the remaining one and check not held
        test_stock.sell(date='2019-12-09', num=9)
        self.assertEqual(test_stock.is_held(), False)
        
        self.assertAlmostEqual(
            test_stock.get_total_buy_cost(),2672.69989, places=2
        )
        
        # 258.309998 * 1 + 270.000000 * 9 
        self.assertAlmostEqual(
            test_stock.get_total_sell_cost(), 2688.309998, places=2
        )
        
        self.assertAlmostEqual(
            test_stock.get_valuation('2019-12-09'), 0., places=2
        )
        
        
    
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
            'EMN', 'UAL', 'V', 'GS', 
            'PYPL','ROK','CLX',  'CVS', 'RL' 
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
        test_stocks = ['AAPL','AMZN','ADBE', 'CVS','VOO', 'VCR']
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
        
        