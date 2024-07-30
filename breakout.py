import logging
import os

import yfinance as yf
import pandas as pd
from pandas import DataFrame

from datetime import datetime


from backtrader import Cerebro
from backtrader.sizers import PercentSizer
from backtrader.feeds import PandasData

from BreakoutStrategy import BreakoutStrategy
from pivot import * 

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
    log_level = None
    ticker = None
   
    pivot_window = Pivot.WINDOW
    
    @staticmethod
    def initialize():
        
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
    def load_data(ticker, b, e):  
        
        if ticker in ['d', 'h', '5m']:
            delimiter = ',' if ticker in ['d', 'h'] else ';'
            data = pd.read_csv(f'data/eurusd_{ticker}.csv', delimiter=delimiter)
            if not 'Date' in data.columns:
                data = data.rename({"Gmt time": "Date"}, axis = 1)
                data.Date = pd.to_datetime(data.Date, format="%d.%m.%Y %H:%M:%S.%f")
                    
            
            if ticker == '5m':
                data.Date = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%d/%m/%Y %H:%M:%S')
                data = data.drop(columns=['Time'])
            
            data.set_index("Date")
           
            if ticker == 'h':
                data = data[data['Volume'] != 0]
                
            data.reset_index(drop=True, inplace=True)    
                    
        else:                   
            Application.ticker = ticker     
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
 
    from backtrader.sizers import PercentSizer       
    
    @staticmethod
    def optimize(data, pivots):
        Application.logger.info(f'optimize: {Application.ticker}...\n')
        pdata = PandasData(dataname=data, datetime=None, open=0, high=1, low=2, close=3, volume=4, openinterest=-1)
        
        Application.logger.info(f'optimize: init cerebro...\n')
        cerebro = Cerebro(stdstats=True)
        cerebro.broker.setcash(1_000_000.0) 
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addsizer(PercentSizer, percents = 90)          
         
        initial_value = cerebro.broker.get_value()
        cerebro.adddata(data=pdata)

        TP_SL_RATIO     = [1.5 + x/10 for x in range(0, 5)]
        SL_DISTANCE     = [0.024 + x/1000 for x in range(0, 3)]    
        BACKCANDLES     = [39, 40]
        ZONE_WIDTH      = [0.019, 0.020, 0.021, 0.022]
        GAP_WINDOW      = range(35, 41)
        
        if GAP_WINDOW.start <= Pivot.WINDOW:
            raise ValueError(f"gap must be greater than pivot window. gap={GAP_WINDOW.start}, pivot window={Pivot.WINDOW}")

        
        Application.logger.info(f'optimize: adding strategy...\n')
        strats = cerebro.optstrategy(
            BreakoutStrategy,
                ticker       = (Application.ticker,),
                tp_sl_ratio  = TP_SL_RATIO,    
                sl_distance  = SL_DISTANCE,
                backcandles  = BACKCANDLES,
                gap_window   = GAP_WINDOW, 
                zone_width   = ZONE_WIDTH,
                pivots       = (pivots,)
            ) 
        
        runs = len(TP_SL_RATIO) * len(SL_DISTANCE) * len(BACKCANDLES) * len(GAP_WINDOW) * len(ZONE_WIDTH)
        print(f"optimize, total number of runs: {runs}\n") 
        Application.logger.info(f'optimize: cerebro...{runs}\n')
        
        from backtrader.analyzers import SharpeRatio, DrawDown, Returns 
        cerebro.addanalyzer(SharpeRatio, _name = "sharpe")
        cerebro.addanalyzer(DrawDown, _name = "drawdown")
        cerebro.addanalyzer(Returns, _name = "returns") 
                  
        results = cerebro.run(maxcpus=1)
        
        par_list = [
            [   x[0].params.tp_sl_ratio,
                x[0].params.sl_distance,
                x[0].params.backcandles,             
                x[0].params.gap_window,
                x[0].params.zone_width,             
                
                x[0].analyzers.returns.get_analysis()['rnorm100'], 
                x[0].analyzers.drawdown.get_analysis()['max']['drawdown'],
                x[0].analyzers.sharpe.get_analysis()['sharperatio']
            ] for x in results 
        ]
        
        par_df = DataFrame(par_list, columns = ['tp-sl', 'stoploss-d', 'back-w', 'gap-w', 'zone-width', 'profit', 'dd', 'sharpe'])
        par_df.to_csv(f'out/{Application.ticker}-results.csv')
                
        end_value = cerebro.broker.get_value()
        profit    = end_value-initial_value
        gain      = 100*profit / initial_value
        
        print(f"\nstart value: {initial_value:8.2f}\nend value: {end_value: 11.2f}\nprofit:{profit:15.2f}\ngain: {gain:16.2f}%")
        
        Application.logger.info(f"START VALUE: {initial_value:8.2f}, END VALUE: {end_value:8.2f}, PROFIT: {profit:8.2f}, PERC: {gain:4.2f}")          
            
        print('\ndone.')
        
    
    @staticmethod
    def run(data, pivots, backcandles, gap, zoneheight, plot: bool = False):  
        if gap <= pivot_window:
            raise ValueError(f"gap must be greater than pivot window. gap={gap}, pivot window={Pivot.WINDOW}")
                 
        Application.logger.info(f'run: {Application.ticker}...\n')
        pdata = PandasData(dataname=data, datetime=None, open=0, high=1, low=2, close=3, volume=4, openinterest=-1)
        
        Application.logger.info(f'run: init cerebro...\n')
        cerebro = Cerebro(stdstats=True)
        cerebro.broker.setcash(10_000.0) 
        #cerebro.broker.setcommission(commission=0.001)
        cerebro.addsizer(PercentSizer, percents = 70)          
        
        initial_value = cerebro.broker.get_value()        

        cerebro.adddata(data=pdata)

    
        GAP_WINDOW      = gap if gap != None else Pivot.WINDOW + 1
        BACKCANDLES     = backcandles if backcandles != None else 40
        SL_DISTANCE     = 0.026
        TP_SL_RATIO     = 1.9
        ZONE_WIDTH      = zoneheight if zoneheight != None else 0.022
        BREAKOUT_FACTOR = 1.84 # mot used
        
        '''
        GAP_WINDOW      = 7
        BACKCANDLES     = 40
        SL_DISTANCE     = 0.03
        TP_SL_RATIO     = 2
        ZONE_WIDTH      = 0.01
        BREAKOUT_FACTOR = 1.84
        '''    
        Application.logger.info(f'run: adding strategy...\n')
        cerebro.addstrategy(
            BreakoutStrategy,
                ticker       = Application.ticker,
                tp_sl_ratio  = TP_SL_RATIO,    
                sl_distance  = SL_DISTANCE,
                backcandles  = BACKCANDLES,
                gap_window   = GAP_WINDOW, 
                zone_width   = ZONE_WIDTH,
                pivots       = pivots
            ) 
            
        #cerebro.addsizer(PercentSizer, percents = 90)   
        Application.logger.info(f'run: cerebro...\n')
              
        cerebro.run()
        
        end_value = cerebro.broker.get_value()
        profit    = end_value-initial_value
        gain      = 100*profit / initial_value
        
        
        print(f"\nstart: \t{data.index[0]}\nend: \t{data.index[-1]}\nduration: \t{data.index[-1]-data.index[0]}\nstart value: \t{initial_value:8.2f}\nend value: \t{end_value:8.2f}\nprofit: \t{profit:8.2f}\ngain: \t{gain:8.2f}%")
        
        Application.logger.info(f"START VALUE: {initial_value:8.2f}, END VALUE: {end_value:8.2f}, PROFIT: {profit:8.2f}, PERC: {gain:4.2f}")
               
        if plot:
            cerebro.plot() 
            
        print('\ndone.')


    
 

def get_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("ticker")
    p.add_argument("begin")
    p.add_argument("end")
    
    p.add_argument("-c", "--config", help="configuration file")
    p.add_argument("-g", "--gap", type=int, help="gap window")
    p.add_argument("-b", "--backcandles", type=int, help="number of bars in zone (backcandles)")
    p.add_argument("-p", "--pwindow", type=int, help="number of bars in pivot window")
    p.add_argument("-z", "--zoneheight", type=float, help="height of zone in fraction of price")
    p.add_argument("-m", "--max", type=int, help="max no of bars from start")
    p.add_argument("-r", "--run", action="store_true", help="normal mode of operation")
    p.add_argument("-o", "--optimize", action="store_true", help="testing parameter combinations")
    p.add_argument("-s", "--save", action="store_true", help="saving input to csv file")
    p.add_argument("-plot", "--plot", action="store_true", help="showing plot of pivots")
    p.add_argument("-l", "--loglevel", help="loglevel (default=INFO)")

    return p.parse_args() 
    


def get_loglevel(loglevel):
    if not loglevel:
        return LOGGING_DEFAULT
    
    return logging.getLevelName(loglevel.upper())





#
# MAIN FUNDTION
#

if __name__ == '__main__': 

    try:
        # read command line
        args = get_args()
                             
        ticker = None
        if args.ticker in ('H', 'D', 'h', 'd', '5m'): 
            Application.ticker = 'EURUSD'
            ticker = args.ticker.lower()
            b = None
            e = None            
        else: 
            ticker = args.ticker.upper()
            Application.ticker = ticker                         
            # mandatory 'begin' and 'end' cmd line arguments                                       
            b = datetime.strptime(args.begin, '%Y%m%d').date()
            e = datetime.strptime(args.end, '%Y%m%d').date()
 
               
        # initialize the application             
        Application.log_level = get_loglevel(args.loglevel)                     
        
        Application.initialize()        
        Application.logger.info("START")    
               
        Application.logger.info("\n")
        Application.logger.info(f'{ticker} start: [{b}, end: {e}]\n')
        

        # load data into pandas DataFrame        
        data = Application.load_data(ticker, b, e) 
        

        # slice input 
     
        
        if ticker.lower() in ['d', 'h', '5m']:   
            data = data[int(args.begin):int(args.end)]
        else:    
            data [0:args.max] if args.max else data[0:]
            
        if args.save:  
            print('saving backup')    
            data.to_csv(f"out/{ticker.lower()}-{args.begin}-{args.end}-backup.csv")          
              
        # pre calculate pivots
        print('calculating pivots...')
        pivot_window = args.pwindow if args.pwindow else Pivot.WINDOW
        data['pivot'] = pivot(data=data, pivot_window=pivot_window)
                
        # plot pivots
        if args.plot:
            pivot_plot(data)
            
        data.set_index("Date", inplace=True, drop=True)
        data.reset_index() 
        
        # backup for reference 
        if args.save:  
            print('saving backup')    
            #data.to_csv(f"out/{ticker.lower()}-{args.begin}-{args.end}-backup.csv")           
        
        # execute (if both options are provided, optimize is ignored)
        if args.run:
            print("run...")
            g = args.gap if args.gap else pivot_window+1
            b = args.backcandles if args.backcandles else 39
            z = args.zoneheight if args.zoneheight else None
            Application.run(data, data['pivot'].array._ndarray, backcandles=b, gap=g, zoneheight=z, plot=args.plot) 
            
        elif args.optimize:
            print("optimize...")
            Application.optimize(data, data['pivot'].array._ndarray) 
            
  
    except Exception as e:
        import traceback
        print(f'something\'s wrong: {e}')
        print(traceback.format_exc())       
        Application.logger.error(e)
    finally:
        Application.logger.info("done.")
        
        
