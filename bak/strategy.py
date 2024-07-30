

from backtrader import Strategy


class BreakoutStrategy(Strategy):
    params = dict(
        tp_sl_ratio = 2,    
        distance = 0.03     # distance 3% below or above current price depending on direction
        )
    
    
    pos_sz = 10000          # position size
   
    
    
    
    def __init__(self):
        
        if self.data == None:
            raise Exception('Set BreakoutStrategy.data to the appropriate DataFrame')
        
        
        self.signal = datas[0].signal
 
 
    def next(self):

        #if len(self.trades) == 1:
        #    for trade in self.trades:
        #        trade.sl = trade.entry_price

        if len(self.trades) == 0:
            
            signal = self.signal[-1]
            match signal:
                case 1: # SELL
                    sl1 = self.data.Close[-1] * (1.0 + self.distance)
                    sl_diff = abs(sl1-self.data.Close[-1])
                    tp1 = self.data.Close[-1] - sl_diff * self.tp_sl_ratio
                    #tp2 = self.data.Close[-1] - sl_diff
                    self.sell(sl=sl1, tp=tp1, size=self.pos_sz)
                    #self.sell(sl=sl1, tp=tp2, size=self.pos_sz)
                    
                case 2: # BUY
                    sl1 = self.data.Close[-1] * (1.0 - self.distance)
                    sl_diff = abs(sl1-self.data.Close[-1])
                    tp1 = self.data.Close[-1] + sl_diff * self.tp_sl_ratio
                    #tp2 = self.data.Close[-1] + sl_diff
                    self.buy(sl=sl1, tp=tp1, size=self.pos_sz)
                    #self.buy(sl=sl1, tp=tp2, size=self.pos_sz)
                
                case 0:
                    pass
                case _:
                    raise ValueError(f'Signal: {signal} is invalid. Should be either 0, 1, or 2')
                          
