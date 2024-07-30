import logging
logger = logging.getLogger()

import statistics
from trading import Signal
from pivot import Pivot

ZONE_N_PIVOTS = 3



class algo:   
    
    @staticmethod
    def is_trend(close, open, ema, backcandles=10):    
        ema_signal = [0.0]*len(close)

        for idx in range(backcandles, len(close)):
            upt = 2 # 0x0010
            dnt = 1 # 0x0001
            
            r = range(idx-backcandles, idx+1)
            for i in r:
                if max(open[i], close[i]) > ema[i]:
                    dnt = 0
                    break
                
            for i in r:               
                if min(open[i], close[i]) < ema[i]:
                    upt = 0
                    break
                    
            ema_signal[idx] = upt | dnt
            
        return ema_signal
    

    @staticmethod
    def slice(data, b, e):
        return data.get(ago=e-data.buflen(), size=e-b)
      

    @staticmethod
    def get_pivots(highlow, data, pivots):
        values = []
        for i in range(0, len(data)):
            if pivots[i] == highlow:
                values.append(data[i])
                
        return values

    @staticmethod
    def get_pivots_high(data, pivots):
        return algo.get_pivots(Pivot.HIGH, data, pivots)

    @staticmethod
    def get_pivots_low(data, pivots):
        return algo.get_pivots(Pivot.LOW, data, pivots)
    
   
    def _check_breakout(f_breakout_test, values, zone_height, cclose):
        
        # helper function: check if pivots form a zone
        def _is_zone(values, mean, height):
            for values in values:
                if abs(values-mean) > height:
                    return False   
            return True


        # main function body    
        mean = statistics.mean(values)
        if _is_zone(values, mean, zone_height):
            return f_breakout_test(mean, cclose, zone_height)           
        
        return Signal.NONE 



    #
    # data          the data feed
    # candle_idx    the current candle
    # backcandles   the width of the window of analysis
    # gap_window    gap must be >= pivot window to make sure pivot window doesn;t extend beyond current candle
    # pivots        the array holding the pivots
    # zone_height   the absolute price fluctuation  
    #
    @staticmethod
    def calc_signal(data, candle_idx, backcandles, gap_window, pivots, zone_height): 
        # gap_window must be >= pivot window to avoid look ahead bias     
        begin = candle_idx - backcandles - gap_window
        end   = candle_idx - gap_window   
        
        if begin < 0 or candle_idx + gap_window >= data.buflen():
            return 0
        
                
        _F = 2.0    # optimal value??
        _N = 3      # number of bounces
        sig = Signal.NONE    
            
        cclose = data.close.array[candle_idx]                     

        lows = data.low.array
        pvts = algo.get_pivots_low(data=lows[begin:end], pivots=pivots[begin:end])[-_N:]
        
        if _N == len(pvts):
            sig = algo._check_breakout(                                             
                    lambda mean, cclose, zheight: (Signal.SELL if (mean - cclose) > zheight * _F else 0), 
                    pvts, 
                    zone_height, 
                    cclose
                )
        
            if sig != Signal.NONE: 
                #print(f"SELL SIGNAL: {candle_idx}")
                return sig
      
      
        highs = data.high.array
        pvts = algo.get_pivots_high(data=highs[begin:end], pivots=pivots[begin:end])[-_N:]
        
        if _N == len(pvts):      
            sig = algo._check_breakout(
                lambda mean, cclose, zheight: (Signal.BUY if (cclose - mean) > zheight * _F else 0),   
                pvts, 
                zone_height, 
                cclose
            )
 
            #if sig != 0: 
            #    print(f"BUY SIGNAL: {candle_idx}")
            
            
        return sig
