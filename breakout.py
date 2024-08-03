import logging
import os

import yfinance as yf
import pandas as pd
from pandas import DataFrame

from datetime import datetime


from backtrader import Cerebro
from backtrader.sizers import PercentSizer
from backtrader.feeds import PandasData
from backtrader.analyzers import SharpeRatio, DrawDown, Returns

from BreakoutStrategy import BreakoutStrategy
from pivot import * 


from parameters import RuntimeParameters, RunParameters, OptimizeParameters, TradingParameters


pd.options.mode.copy_on_write = True
LOGGING_DEFAULT = logging.INFO

def make_dirs(path: str):
    if not os.path.exists(path):
        os.makedirs(path)





class Application :
    CONFIG_DIR = 'conf'
    OUTPUT_DIR = 'out'
    LOGGING_DIR = 'log'
    NOW = pd.Timestamp.today().replace(microsecond=0)    

    logger = logging.getLogger()
    log_level = LOGGING_DEFAULT
    ticker = None
   
    pivot_window = Pivot.WINDOW
    
    @staticmethod
    def initialize() -> None:
        
        # create directories    
        make_dirs(Application.OUTPUT_DIR)
        make_dirs(Application.LOGGING_DIR)
        
        # create log file
        logging.basicConfig(
            filename=f'{Application.LOGGING_DIR}/{__name__}{Application.NOW}.log',
            format='%(levelname)s %(name)s: %(asctime)s %(message)s',
            filemode='w')       

        Application.logger.setLevel(Application.log_level)
               
    
    @staticmethod
    def load_testdata(ticker: str, b, e) -> DataFrame:
        delimiter = ';' if ticker in ['5m', '5M'] else ','
        data = pd.read_csv(f'data/eurusd_{ticker}.csv', delimiter=delimiter)
        if not 'Date' in data.columns:
            data = data.rename({"Gmt time": "Date"}, axis = 1)
            data.Date = pd.to_datetime(data.Date, format="%d.%m.%Y %H:%M:%S.%f")
                
        
        if ticker == '5m':
            data.Date = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%d/%m/%Y %H:%M:%S')
            data = data.drop(columns=['Time'])
        
        data.set_index("Date")
        
        # remove empty data
        if ticker == 'h':
            data = data[data['Volume'] != 0]             
            
        data = data[b:e] if e not in [-1] else data[b:]        
        data.reset_index(drop=True, inplace=True)    
                
        if len(data) == 0:
            raise Exception(f'No data for ticker: {ticker}')              
        return data
 
    @staticmethod
    def fetch_data(ticker: str, b: int, e: int) -> DataFrame:  
        data = yf.download(ticker, start=b, end=e)             
        data.reset_index(inplace = True, drop = False)
        if "Date" in data.columns:  
            data.set_index("Date")
          
        if len(data) == 0:
            raise Exception(f'No data for ticker: {ticker}')       
        return data
    
    @staticmethod
    def save_snapshot(data):
        data.to_csv(f'{Application.OUTPUT_DIR}/{Application.NOW.date().strftime("%Y%m%d")}_{Application.ticker}_snapshot.csv', sep='\t')
    
    
    @staticmethod
    def get_filename(name):
        return f'{Application.OUTPUT_DIR}/{Application.NOW.date().strftime("%Y%m%d")}_{Application.ticker}_{name}_results.csv'
    
 
    @staticmethod
    def result():
        pass
 
 
    @staticmethod
    def save_optim_results(results):
        par_list = [
                [   x[0].params.tp_sl_ratio,
                    x[0].params.sl_distance,
                    x[0].params.backcandles,             
                    x[0].params.gap_window,
                    x[0].params.zone_height, 
                    x[0].params.breakout_f,            
                    
                    x[0].analyzers.returns.get_analysis()['rtot'], 
                    x[0].analyzers.returns.get_analysis()['rnorm100'], 
                    x[0].analyzers.drawdown.get_analysis()['max']['drawdown'],
                    x[0].analyzers.sharpe.get_analysis()['sharperatio']
                ] for x in results 
            ]
            
        par_df = DataFrame(par_list, columns = ['tp-sl', 'stoploss-d', 'back', 'gap', 'zone-height', 'bof', 'total', 'yearly', 'max-dd', 'sharpe'])
        par_df.to_csv(f'out/{Application.ticker}-{Application.NOW.date().strftime("%Y%m%d")}-results.csv')    
    
        
 
    from backtrader.sizers import PercentSizer       
    
    @staticmethod
    def optimize(data: DataFrame, par: OptimizeParameters, trading_par: TradingParameters):
        Application.logger.info(f'optimize: {Application.ticker}...\n')
        pivots = data['pivot'].array._ndarray
        pdata = PandasData(dataname=data, datetime=None, open=0, high=1, low=2, close=3, volume=4, openinterest=-1)
        
        Application.logger.info(f'optimize: init cerebro...\n')
        cerebro = Cerebro(stdstats=True)
        
        cerebro.broker.setcash(trading_par.amount) 
        cerebro.broker.setcommission(trading_par.commission)
        cerebro.addsizer(PercentSizer, percents = 100 * trading_par.size) 
        BreakoutStrategy.LONG = trading_par.plong
        BreakoutStrategy.SHORT = trading_par.pshort
                    
         
        cerebro.adddata(data=pdata)

        Application.logger.info(f"optimize, par.zone_height, {par.zone_height}")

        Application.logger.info(f'optimize: adding strategy...\n')
        
         
        print(par.zone_height)
        strats = cerebro.optstrategy(
            BreakoutStrategy,
                ticker       = (Application.ticker,),
                
                tp_sl_ratio  = par.tp_sl_ratio,    
                sl_distance  = par.sl_distance,
                backcandles  = par.backcandles,
                gap_window   = par.gap_window, 
                zone_height  = par.zone_height,
                breakout_f   = par.breakout_factor,
                
                pivots       = (pivots,)
            ) 
                
        runs = len(par.tp_sl_ratio) * len(par.sl_distance) * len(par.backcandles) * len(par.gap_window) * len(par.zone_height)
        print(f"optimize, total number of runs: {runs}\n") 
        Application.logger.info(f'optimize: cerebro...{runs}\n')
        
        cerebro.addanalyzer(SharpeRatio, _name = "sharpe")
        cerebro.addanalyzer(DrawDown, _name = "drawdown")
        cerebro.addanalyzer(Returns, _name = "returns") 
         
        initial_value = cerebro.broker.get_value()                 
        results = cerebro.run(maxcpus=1)                        
        end_value = cerebro.broker.get_value()
        
        profit    = end_value-initial_value
        gain      = 100*profit / initial_value
        
        print(f"\nstart value: {initial_value:8.2f}\nend value: {end_value: 11.2f}\nprofit:{profit:15.2f}\ngain: {gain:16.2f}%")
        Application.logger.info(f"START VALUE: {initial_value:8.2f}, END VALUE: {end_value:8.2f}, PROFIT: {profit:8.2f}, PERC: {gain:4.2f}")    
            
        Application.save_optim_results(results)  
                 
        print('\ndone.')
        
    
    @staticmethod
    def run(data: DataFrame, par: RunParameters, trading_par: TradingParameters, plot: bool = False):  
          
        Application.logger.info(f'run: {Application.ticker}...\n')
        pivots = data['pivot'].array._ndarray    
        pdata = PandasData(dataname=data, datetime=None, open=0, high=1, low=2, close=3, volume=4, openinterest=-1)
        
        Application.logger.debug(f'run: init cerebro...\n')
        cerebro = Cerebro(stdstats=True)
        
        cerebro.broker.setcash(trading_par.amount) 
        print(f'amount: {trading_par.amount}, commission: {trading_par.commission}, long: {trading_par.plong}, short: {trading_par.pshort}, size: {trading_par.size}')
        cerebro.broker.setcommission(trading_par.commission)
        cerebro.addsizer(PercentSizer, percents = 100 * trading_par.size) 
        BreakoutStrategy.LONG = trading_par.plong
        BreakoutStrategy.SHORT = trading_par.pshort

        cerebro.adddata(data=pdata)

        Application.logger.debug(f'run: adding strategy...\n')
        cerebro.addstrategy(
            BreakoutStrategy,
                ticker       = Application.ticker,
                
                tp_sl_ratio  = par.tp_sl_ratio,   
                sl_distance  = par.sl_distance,
                backcandles  = par.backcandles,
                gap_window   = par.gap_window, 
                zone_height  = par.zone_height,
                breakout_f   = par.breakout_factor,
                
                pivots       = pivots
            ) 
            
        cerebro.addanalyzer(SharpeRatio, _name = "sharpe")
        cerebro.addanalyzer(DrawDown, _name="drawdown")
        cerebro.addanalyzer(Returns, _name = "returns")
        
        Application.logger.debug(f'run: cerebro...\n')
              
        initial_value = cerebro.broker.get_value()       
        results = cerebro.run()
        end_value = cerebro.broker.get_value()
        
        par_list = [
                [   x.analyzers.returns.get_analysis()['rtot'], 
                    x.analyzers.returns.get_analysis()['rnorm100'], 
                    x.analyzers.drawdown.get_analysis()['max']['drawdown'],
                    x.analyzers.sharpe.get_analysis()['sharperatio']
                ] for x in results 
            ]

        print()
        par_df = DataFrame(par_list, columns = ['total', 'yearly', 'max-dd', 'sharpe',])
        print(par_df)
               
        profit    = end_value-initial_value
        gain      = 100.0 * profit / initial_value
               
        print(f"\nstart: \t{data.index[0]}\nend: \t{data.index[-1]}\nduration: \t{data.index[-1]-data.index[0]}\nstart value: \t{initial_value:8.2f}\nend value: \t{end_value:8.2f}\nprofit: \t{profit:8.2f}\ngain: \t{gain:8.2f}%")        
        Application.logger.info(f"START VALUE: {initial_value:8.2f}, END VALUE: {end_value:8.2f}, PROFIT: {profit:8.2f}, PERC: {gain:4.2f}")
               
        if plot:
            cerebro.plot() 
            
        print('\ndone.')


    
 

def get_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("ticker")
    p.add_argument("begin", help="for test data, first bar, else start date")
    p.add_argument("end", help="for test data, stop bar (e=-1 indicates e is ignored), else stop date")
    
    p.add_argument("-c", "--config", help="configuration file (json)")
    p.add_argument("-g", "--gap", type=int, help="gap window")
    p.add_argument("-b", "--backcandles", type=int, help="number of bars in zone (backcandles)")
    p.add_argument("-p", "--pwindow", type=int, help="number of bars in pivot window")
    p.add_argument("-z", "--zoneheight", type=float, help="height of zone in fraction of price")
    p.add_argument("-m", "--max", type=int, help="max no of bars from start")
    p.add_argument("-r", "--run", action="store_true", help="normal mode of operation")
    p.add_argument("-s", "--save", action="store_true", help="saving input to csv file")
    p.add_argument("-plot", "--plot", action="store_true", help="showing plot of pivots")
    p.add_argument("-log", "--loglevel", help="loglevel (default=INFO)")

    return p.parse_args() 
    


def get_loglevel(loglevel):
    if not loglevel:
        return LOGGING_DEFAULT
    
    return logging.getLevelName(loglevel.upper())


    


#
# MAIN FUNDTION
#
from plotting import pivot_plot
import config
from config import Config, RuntimeOptions, RunOptions

if __name__ == '__main__': 
    
    TEST = ['h', 'd', '5m', 'H', 'D', '5M']

    try:
        # read command line
        args = get_args()
        
        Application.log_level = get_loglevel(args.loglevel)                            
        Application.initialize()     
        
        Application.logger.info("START")                  
                
        data = None                     
        ticker = None
              
        # loading data    
        print("loading data...")    
        if args.ticker in TEST: 
            Application.ticker = 'EURUSD'
            ticker = args.ticker.lower()
            begin = int(args.begin) 
            end = int(args.end) 
            Application.logger.info(f'data = {ticker}, [start, end] = [{begin}, {end}]\n')
            data = Application.load_testdata(ticker, begin, end) 
        else: 
            ticker = args.ticker.upper()
            Application.ticker = ticker                         
            # mandatory 'begin' and 'end' cmd line arguments                                       
            bdate = datetime.strptime(args.begin, '%Y%m%d').date()
            edate = datetime.strptime(args.end, '%Y%m%d').date()
            Application.logger.info(f'data = {ticker}, [start, end] = [{bdate}, {edate}]\n')
            data = Application.fetch_data(ticker, bdate, edate) 
                       
    
        # pre calculate pivots
        print('calculating pivots...')
        pivot_window = args.pwindow if args.pwindow else Pivot.WINDOW
        data['pivot'] = pivot(data=data, pivot_window=pivot_window)
                
        # plot pivots
        if args.plot:
            pivot_plot(data)
            
        data.set_index("Date", inplace=True, drop=True)
        data.reset_index()         
        
        #
        # using specified config file 
        #  
        if args.config:
            configuration: Config = config.load_config(args.config)            
            opt = RuntimeParameters(configuration.runtime) 
            
            if opt.SAVE_SNAPSHOT: 
                data.to_csv(f"out/{ticker.lower()}-{args.begin}-{args.end}-backup.csv")            
            
            if opt.STORE_SIGNALS:
                pass
            
            if opt.STORE_ACTIONS: 
                pass
            
            if opt.RUN: 
                run = RunParameters(conf=configuration.run)
                trading = TradingParameters(conf=configuration.trading)
                Application.run(data=data, par=run, trading_par=trading, plot=opt.PLOTTING) 
             
            elif opt.OPTIMIZE:
                optim = OptimizeParameters(conf=configuration.optim)
                trading = TradingParameters(conf=configuration.trading)
                Application.optimize(data=data, par=optim, trading_par=trading)
                         
 
 
 
        #
        # command line options
        #        
        
        else:                    
            # backup for reference            
            if args.save:  
                print('saving backup...')    
                data.to_csv(f"out/{ticker.lower()}-{args.begin}-{args.end}-backup.csv")          
                
 
           
            # execute 
            if args.run:
                print("run...")
                opt = RunOptions()
                
                if args.gap is not None:
                    opt.add(tag='gap_window', value=int(args.gap)) 
                if args.backcandles is not None:
                    opt.add(tag='backcandles', value=int(args.backcandles)) 
                if args.pwindow is not None:
                    opt.add(tag='pivot_window', value=int(args.pwindow)) 
                if args.zoneheight is not None:
                    opt.add(tag='zone_height', value=float(args.zoneheight)) 
                
                parameters = RunParameters(conf=opt)
                tradingpar = TradingParameters(None)#conf=config.TradingOptions.default())
                Application.run(data=data, par=parameters, trading_par=tradingpar, plot=args.plot) 
                   
            
            
  
    except Exception as e:
        import traceback
        print(f'something\'s wrong: {e}')
        print(traceback.format_exc())       
        Application.logger.error(e)
    finally:
        Application.logger.info("done.")
        
        
