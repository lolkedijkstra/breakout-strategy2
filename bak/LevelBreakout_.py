import logging
import sys
import os

import yfinance as yf
import pandas as pd
from pandas import DataFrame
import numpy as np
import plotly.graph_objects as go
from scipy import stats
from datetime import datetime


import backtrader as bt
from backtrader import Cerebro
from backtrader.sizers import PercentSizer
from backtrader.feeds import PandasData

from BreakoutStrategy import BreakoutStrategy

pd.options.mode.copy_on_write = True

LOGGING_LEVEL = logging.DEBUG

TICKER = 'EURUSD.X'

def create_dir_if_not_exists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)




class Application :
    CONFIG_DIR = 'conf'
    OUTPUT_DIR = 'out'
    LOGGING_DIR = 'log'
    NOW = pd.Timestamp.today().replace(microsecond=0)    

    logger = logging.getLogger()
    ticker = None
   
    
    @staticmethod
    def initialize():
        
        # create directories    
        create_dir_if_not_exists(Application.OUTPUT_DIR)
        create_dir_if_not_exists(Application.LOGGING_DIR)
        
        # create log file
        logging.basicConfig(
            filename=f'{Application.LOGGING_DIR}/{__name__}{Application.NOW}.log',
            format='%(levelname)s %(name)s: %(asctime)s %(message)s',
            filemode='w')       

        Application.logger.setLevel('INFO')
               
    
    @staticmethod
    def load_data(ticker, b, e):  
        
        if ticker == 'EURUSD':
            data = pd.read_csv('data/eurusd.csv')
            data = data.rename({"Gmt time": "Date"}, axis = 1)
            data.Date = pd.to_datetime(data.Date, format="%d.%m.%Y %H:%M:%S.%f")
            data.set_index("Date")
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
    def run(data, pivots, plot: bool = False):
        Application.logger.info(f'run: {Application.ticker}...\n')
        #pivots = data['pivot']
        pdata = PandasData(dataname=data, datetime=None, open=0, high=1, low=2, close=3, volume=4, openinterest=-1)
        
        Application.logger.info(f'run: init cerebro...\n')
        cerebro = Cerebro(stdstats=True)
        cerebro.broker.setcash(100_000.0) 
        cerebro.broker.setcommission(commission=0.001)
        
        initial_value = cerebro.broker.get_value()
        cerebro.adddata(data=pdata)

        Application.logger.info(f'run: adding strategy...\n')
        cerebro.addstrategy(
            BreakoutStrategy,
            ticker      = TICKER,
            tp_sl_ratio = 2,    
            distance    = 0.03,
            pivots      = pivots, #.array,
            zone_width  = 0.01
            ) 
            
        #cerebro.addsizer(PercentSizer, percents = 90)   
        Application.logger.info(f'run: cerebro...\n')
              
        cerebro.run()
        
        
        latest_value = cerebro.broker.get_value()
        profit = latest_value-initial_value
        gain = 100*profit / initial_value
        
        print(f"Start value: {initial_value:8.2f}\nEnd value: {latest_value: 11.2f}\nProfit:{profit:15.2f}\nGain: {gain:16.2f}%")
        Application.logger.info(f"START VALUE: {initial_value:8.2f}, END VALUE: {latest_value:8.2f}, PROFIT: {profit:8.2f}, PERC: {gain:4.2f}")
        
        
        print (cerebro.broker.getvalue())  
        if plot:
            cerebro.plot() 


    
 
#
#
#

def pivot_candle(data, candle_idx, window) -> int:
    """
    function that detects if a candle is a pivot/fractal point
    args: candle index, window before and after candle to test if pivot
    returns: 1 if pivot high, 2 if pivot low, 3 if both and 0 default
    """
    if candle_idx < window or (candle_idx + window) >= len(data):
        return 0
    
    r = range(candle_idx-window, candle_idx+window+1)
    
    pivot_low = 2  
    for i in r:
        if data.iloc[i].Low < data.iloc[candle_idx].Low:
            pivot_low = 0
            break
            
    pivot_high = 1
    for i in r:           
        if data.iloc[i].High > data.iloc[candle_idx].High:
            pivot_high = 0
            break
            
    return pivot_high | pivot_low        

def pivot(data, window):
    return data.apply(lambda x: pivot_candle(data, x.name, window), axis=1)   


'''
def _is_lh_candle(df, candle_idx, window, lh_indicator: int):
    if candle_idx < window or (candle_idx + window) >= len(df):
        return False
    
    r = range(candle_idx-window, candle_idx+window+1)
    
    match lh_indicator:
        case 2: #low
            for i in r:
                if df.iloc[candle_idx].Low > df.iloc[i].Low:
                    return False
                
        case 1: # high
            for i in r:           
                if df.iloc[candle_idx].High < df.iloc[i].High:
                    return False
          
    return True
    
    
def is_pivot_h(df, window):
    return df.apply(lambda x: _is_lh_candle(df, x.name, window, 1), axis=1)
        

def is_pivot_l(df, window):
    return df.apply(lambda x: _is_lh_candle(df, x.name, window, 2), axis=1)


#
#
#
def show_pivot_plot(data, is_high, is_low):
    delta = 1e-3   
    deltaY = [np.nan] * len(data)
    
    #data.at[idx,'delta-y'] = data.iloc[idx]['High'] + delta

    for idx in range(0, len(data)):
        if is_high[idx]:
             deltaY[idx] = data.iloc[idx]['High'] + delta
        elif is_low[idx]:
            deltaY[idx] = data.iloc[idx]['Low'] - delta

     

    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])

    fig.add_scatter(
        x=data.index, 
        y=deltaY,#y=data['delta-y'], 
        mode="markers",
        marker=dict(size=5, color="MediumPurple"),
        name="pivot")

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.show()

'''   


#
#
#
def show_pivot_plot(dfpl):
    
    def ypos(x):
        return x['Low']-1e-3 if x['pivot']==2 else x['High']+1e-3 if x['pivot']==1 else np.nan

    dfpl['delta-y'] = dfpl.apply(lambda row: ypos(row), axis=1)

    fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                open=dfpl['Open'],
                high=dfpl['High'],
                low=dfpl['Low'],
                close=dfpl['Close'])])

    fig.add_scatter(
        x=dfpl.index, 
        y=dfpl['delta-y'], 
        mode="markers",
        marker=dict(size=5, color="MediumPurple"),
        name="pivot")

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.show()

 

def usage():
    print("USAGE: ticker start_date end_date [config.json]")
                

#
# MAIN FUNDTION
#
import traceback

PIVOT_WINDOW = 6

if __name__ == '__main__':
    #
    # initialize the application
    #
 
 
    if len(sys.argv) < 2:
        usage() 
        sys.exit(0)
    
    
    #
    # cmd line args: ticker from_date to_date [config.json]     
    # 
           
    try:
        TICKER = sys.argv[1].upper()   
               
        if TICKER == 'TEST' or TICKER == 'EURUSD':
            b = '20030505'
            e = '20231028'
            TICKER = 'EURUSD'
        else:  
            if len(sys.argv) < 4:
                usage() 
                sys.exit(0)
             
            # mandatory 'begin' and 'end' cmd line arguments                                       
            b = datetime.strptime(sys.argv[2], '%Y%m%d').date()
            e = datetime.strptime(sys.argv[3], '%Y%m%d').date()
            
        
        Application.ticker = TICKER             
        
        Application.initialize()        
        Application.logger.info("START")    
               
        Application.logger.info("\n")
        Application.logger.info(f'{TICKER} start: [{b}, end: {e}]\n')
        
        # Load data into pandas DataFrame        
        df = Application.load_data(TICKER, b, e) 

        # Limit data
        data = df[0:5000]
              
        # 
        # Pre calculate pivots
        #

        data['pivot'] = pivot(data=data, window=PIVOT_WINDOW)
        #data[data['pivot']!=0].to_csv("out/pivots.csv")
               
        show_pivot_plot(dfpl=data)
            
        data.set_index("Date", inplace=True, drop=True)
        data.reset_index() 
        
        print(data[0:10])       
        Application.run(data, data['pivot'].array._ndarray) 
  
    except Exception as e:
        print(f'That\'s an error: {e}')
        print(traceback.format_exc())       
        Application.logger.error(e)
    finally:
        Application.logger.info("DONE")
        
        