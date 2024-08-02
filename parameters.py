import config
from pivot import Pivot

class RunParameters:  
    
    def __init__(self, conf: config.RunOptions):
        # defaults
        self.pivot_window: int = Pivot.WINDOW
        self.gap_window: int = self.pivot_window + 1
        self.backcandles: int = 40
        self.sl_distance: float = 0.025
        self.tp_sl_ratio: float = 1.9
        self.zone_height: float = 0.001
        self.breakout_factor: float = 1.84        
            
        self.rsi_period: int = 14      
        self.open_long_rsi: float = 31
        self.close_long_rsi: float = 95
        self.open_short_rsi: float = 85
        self.close_short_rsi: float = 17
        
        # copy provided parameters
        tag = "pivot_window"    
        if conf.has(tag):            
            self.pivot_window: int = conf.get(tag)
         
        tag = "gap_window"    
        if conf.has(tag):            
            self.gap_window: int = conf.get(tag)
        
        tag = "backcandles"
        if conf.has(tag):            
            self.backcandles: int = conf.get(tag)
        
        tag = "sl_distance"
        if conf.has(tag):            
            self.sl_distance: float = conf.get(tag)
        
        tag = "tp_sl_ratio"
        if conf.has(tag):            
            self.tp_sl_ratio: float = conf.get(tag)
        
        tag = "zone_height"
        if conf.has(tag):            
            self.zone_height: float = conf.get(tag)
        
        tag = "breakout_factor"
        if conf.has(tag):            
            self.breakout_factor: float = conf.get(tag)
        
        tag = "rsi_period"
        if conf.has(tag):            
            self.rsi_period: int = conf.get(tag)
        
        tag = "open_long_rsi"
        if conf.has(tag):            
            self.open_long_rsi: float = conf.get(tag)
        
        tag = "close_long_rsi"
        if conf.has(tag):            
            self.close_long_rsi: float = conf.get(tag)
        
        tag = "open_short_rsi"
        if conf.has(tag):            
            self.open_short_rsi: float = conf.get(tag)
        
        tag = "close_short_rsi"
        if conf.has(tag):            
            self.close_short_rsi: float = conf.get(tag)
               

class OptParameters:    
    
    def __init__(self, conf: config.Optimize): 
        # defaults
        self.pivot_window   = [Pivot.WINDOW] 
        self.gap_window     = [Pivot.WINDOW+1]
        self.backcandles    = [39, 40]
        self.sl_distance    = [0.024 + x/1000 for x in range(0, 3)] 
        self.tp_sl_ratio    = [1.5 + x/10 for x in range(0, 5)]
        self.zone_height    = [0.00090, 0.00095, 0.00100]    
        self.breakout_factor = [1.84 + x/25 for x in range(0, 5)]
        
        #self.rsi_period
        #self.open_long_rsi
        #self.close_long_rsi
        #self.open_short_rsi
        #self.close_short_rsi
        
        # copy provided parameters
        tag = 'backcandles'
        if conf.has(tag):
            self.backcandles = conf.get(tag)
        
        tag = 'sl_distance'
        if conf.has(tag):
            self.sl_distance = conf.get(tag)
            
        tag = 'tp_sl_ratio'
        if conf.has(tag):
            self.tp_sl_ratio = conf.get(tag)
                   
        tag = 'zone_height'
        if conf.has(tag):
            self.zone_height = conf.get(tag)
        
        tag = 'breakout_factor'
        if conf.has(tag):
            self.breakout_factor = conf.get(tag)
        


