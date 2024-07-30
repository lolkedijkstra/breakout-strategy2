import sys

from backtrader import Strategy
from trading import Signal
from algo import algo
import backtrader as bt
#from backtrader.order import StopLimitBuyOrder, StopBuyOrder, SellOrder, StopSellOrder, StopTrail, StopTrailLimit

#
# logging
#
import logging
logger = logging.getLogger()


def log_signal(level, i, data, signal):
    name = "BUY" if signal == Signal.BUY else "SELL" if signal == Signal.SELL else "NONE" 
    logger.log(level, f'{i}, {data.open.array[i]}, {data.high.array[i]}, {data.low.array[i]}, {data.close.array[i]}, {data.volume.array[i]}, {name}')

def log_signals(level, data, signals, s):
    if level < logger.level:
        return
    
    sz = len(signals)
    
    match(s):
        case Signal.BUY:
            for i in range(0, sz):
                if Signal.BUY == int(signals[i]):
                    log_signal(level, i, data, signals[i])
                    
        case Signal.SELL:
            for i in range(0, sz):
                if Signal.SELL == int(signals[i]):
                    log_signal(level, i, data, signals[i])
                    
        case Signal.EITHER:
            for i in range(0, sz):
                if int(signals[i] in [Signal.BUY, Signal.SELL] ):
                    log_signal(level, i, data, signals[i])
                   




#MAX_OPEN    = 2

class BreakoutStrategy(Strategy):
    
    LOG_INIT = False
    LOG_ORDERS = False

    LOG_LEVEL = logging.INFO

    run_nr = 0
    
    #
    # input parameters for the BreakoutStrategy class
    # these parameters need to be set in the main program and 
    # can be used with optimize to get the optimal value combinations
    #
    params = dict(
        ticker      = None,
        tp_sl_ratio = 0,    
        sl_distance = 0,         # distance % below or above current price depending on direction
        
        #
        # the following parameters will be received from cerebro
        #
        
        backcandles  = 0,     
        gap_window   = 0, 
        pivot_window = 0,     
        zone_width   = 0, 
        pivots       = []               
    )   
     
     
    #
    # BreakoutStrategy.log
    #
    def log(self, txt, dt=None):        
        dt = dt or self.data.datetime.date(0)
        logger.log(BreakoutStrategy.LOG_LEVEL, '%s, %s' % (dt.isoformat(), txt))

    
    def calc_signals(self):        
        from array import array
        sz = self.data.buflen()
        l_signal = array('i', [0] * sz)  
                
        for idx in range(0, sz):
            l_signal[idx] = algo.calc_signal(
                    data        = self.data, 
                    candle_idx  = idx,  
                    backcandles = self.params.backcandles, 
                    gap_window  = self.params.gap_window,
                    pivots      = self.params.pivots,
                    zone_height = self.params.zone_width
                    )
    
             
        return l_signal
    
    
    
    #
    # BreakoutStrategy.__init__
    #
    def __init__(self):  
                       
        logger.info(f"Calculating signals...{BreakoutStrategy.run_nr}")
        
        # keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
               
        self.open_positions = 0 # the idea is to allow multiple orders in parallel up to MAX_OPEN
               
        #self.data['EMA'] = bt.indicators.ExponentialMovingAverage
        #self.data['ema_signal'] = is_trend(self.data, backcandles=10)
        

        # get signals and reset signal index
        self.signal_idx = 0
        self.signals = self.calc_signals()
             
        log_signals(logging.INFO, self.data, self.signals,  Signal.BUY | Signal.SELL )
        
    
    def get_signal(self):
        return self.signals[self.signal_idx]
   
    
    def start(self):
        #sys.stdout.write(f'\rrun nr: {BreakoutStrategy.run_nr}')
        BreakoutStrategy.run_nr = BreakoutStrategy.run_nr + 1
    

    def next(self):
        # log current close
        #self.log(f'Close price: {self.data.close[0]:8.4f}')

        #if len(self.trades) == 1:
        #    for trade in self.trades:
        #        trade.sl = trade.entry_price

        # pending order
        if self.order:
            return

        if not self.position:   # Check if we are in the market
        #if self.open_positions <= MAX_OPEN:  
            close = self.data.close[0]          # last close
            s_fac = self.params.sl_distance     # stop distance as fraction of last close
            r     = self.params.tp_sl_ratio     # w/l ratio
            
            match self.get_signal(): 
                
                case Signal.SELL: 
                    stop1  = close * (1.0 + s_fac)
                    limit1 = close * (1.0 - r * s_fac)   
                    
                    self.log(f'OPEN SELL [close={close:6.4f}, stoploss={stop1:6.4f}, limit={limit1:6.4f}]')               
                    self.order = self.sell_bracket(limitprice=limit1, stopprice=stop1, size=None)
                    
                    #tp2 = close - sl_diff
                    #self.sell(sl=sl1, tp=tp2, size=self.pos_sz)
                    
                case Signal.BUY:
                    stop1  = close * (1.0 - s_fac)
                    limit1 = close * (1.0 + r * s_fac)
                    
                    self.log(f'OPEN BUY [close={close:6.4f}, stoploss={stop1:6.4f}, limit={limit1:6.4f}]')               
                    self.order = self.buy_bracket(limitprice=limit1, stopprice=stop1, size=None)
                    #self.order = self.buy_bracket(exectype=bt.Order.StopTrail, trailpercent=2*s_fac, limitprice=limit1)
                    
                    #tp2 = close + sl_diff
                    #self.buy(sl=sl1, tp=tp2, size=self.pos_sz)
                
                case 0:
                    pass
                case _:
                    raise ValueError(f'Signal: {self.get_signal()} is invalid. Should be either 0, 1, or 2')
         
        else:  # we have a current position
            pass 
         
        # incr signal index 
        self.signal_idx = self.signal_idx+1
        
        

    def notify_order(self, order):        
        
        if order.status in [order.Submitted, order.Accepted]:
            return
                  
        
        # order completed
        if order.status in [order.Completed]:
            # BUY
            if order.isbuy():       
                self.log(f'BUY EXECUTED [Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}]')
                   
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                
            # SELL    
            elif order.issell():    
                self.log(f'SELL EXECUTED [Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}]')

            self.open_positions = self.open_positions +1
            self.bar_executed = len(self)


        elif order.status == order.Canceled:
            self.log('Order Canceled')
        elif order.status == order.Margin:
            self.log('Order Margin')
        elif order.status == order.Rejected:
            self.log('Order Rejected')
            
        # Write down: no pending order
        self.order = None
       
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.open_positions = self.open_positions -2

        print(f'open {trade.baropen:5d}, close {trade.barclose:5d}, profit gross {trade.pnl:8.3f}, net {trade.pnlcomm:8.3f}')
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:8.3f}, NET {trade.pnlcomm:8.3f}\n******')
    

       
