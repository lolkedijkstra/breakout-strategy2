import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel('INFO')



#
# range in json consist of 3 values, begin, end, step, otherwise its an array
#



class _Options:
           
    def __init__(self, json_p):
        self.nodes = dict()
        self.jsp = json_p
       
    def add_node(self, tag):
        fld = self.jsp.get(tag)
        if fld:
            self.nodes[tag] = fld

    def get(self, tag):
        return self.nodes.get(tag)
    

class Options(_Options):
    tags = [
        'save_snapshot','store_signals','store_actions','optimize','run','plotting'
    ]        
       
class RunOptions(_Options):
    tags = [
        'pivot_window',
        'gap_window',
        'backcandles',
        
        'sl_distance',
        'tp_sl_ratio',
        'zone_height',
        'breakout_factor',
        
        'rsi_period',
        
        'open_long_rsi',
        'close_long_rsi',

        'open_short_rsi',
        'close_short_rsi'
    ]
           
class TradingOptions(_Options):
    tags = [
        'amount', 'size', 'long', 'short'
    ]   
         
          
class Optimize:
    @staticmethod
    def _make_array_int(fld):
        if len(fld) == 3 and fld[2] < fld[1]: 
            return list(range(fld[0], fld[1], fld[2]))
        
        return fld

    @staticmethod
    def _make_array_float(fld):
        if len(fld) == 3 and fld[2] < fld[1]: 
            sz = round((fld[1] - fld[0])/fld[2])
            return ( [fld[0] + fld[2] * x for x in range(0, sz)] )
    
        return fld

    
    def __init__(self, json_p):
        self.nodes = dict()
        self.jsp = json_p
       
    def add_float(self, tag):
        fld = self.jsp.get(tag)
        if fld:
            self.nodes[tag] = Optimize._make_array_float(fld)
        
    def add_int(self, tag):
        fld = self.jsp.get(tag)
        if fld:
            self.nodes[tag] = Optimize._make_array_int(fld)

    def get(self, tag):
        return self.nodes.get(tag)
      
 

class Config:
    def __init__(self, opt: Options, run: RunOptions, optim: Optimize, trading: TradingOptions):
        self.opt = opt        
        self.run = run
        self.optim = optim
        self.trading = trading
        
   



def load_config(configfile: str) -> Config:
    logger.info("load_config: start")

    opt: Options = None
    run: RunOptions = None
    tra: TradingOptions = None
    optim: Optimize = None
    

    try:
        with open(configfile, "r") as fconf:
            c = json.load(fconf)     
             
            if not c['options'] is None:      
                opt = Options(c['options'])
                for tag in Options.tags:
                    opt.add_node(tag)
                
            if not c['run'] is None:
                run = RunOptions(c['run'])
                for tag in RunOptions.tags:
                    run.add_node(tag)
                    
            if not c['optimize'] is None:
                optim = Optimize(c.get('optimize'))
                
                optim.add_int('backcandles')               
                optim.add_int('open_long_rsi')
                optim.add_int('close_long_rsi')
                optim.add_int('open_short_rsi')
                optim.add_int('close_short_rsi')
 
                optim.add_float('sl_distance')
                optim.add_float('tp_sl_ratio')
                optim.add_float('zone_height')
                optim.add_float('breakout_factor')
                
                		
            if not c['trading'] is None:
                tra = TradingOptions(c['trading'])
                for tag in TradingOptions.tags:
                    tra.add_node(tag)

 
            
    except Exception as e:
        logger.error(f'\t{e} {fconf}')
        
        
    logger.info("load_config: end\n")
    
    return Config(opt=opt, run=run, optim=optim, trading=tra)  


'''
def check_options():    
    assert( Options.save_snapshot == True )
    assert( Options.store_signals == True )
    assert( Options.store_actions == True )
    
    assert( Options.optimize  == True )
    assert( Options.run == True )
    assert( Options.plotting == False )  
    

def check_run():
    assert( Run.backcandles == 40 )
    assert( Run.sl_distance == 0.025 )
    assert( Run.tp_sl_ratio == 1.9 )
    assert( Run.zone_height == 0.002 )
    assert( Run.breakout_factor == 1.84 )
    assert( Run.rsi_period == 14 )
    assert( Run.open_long_rsi == 31 )
    assert( Run.close_long_rsi == 95 )
    assert( Run.open_short_rsi == 85 )
    assert( Run.close_short_rsi == 17 )


def check_optim():        
    assert ( Optimize.backcandles == [36, 37, 38, 39] )
    assert ( Optimize.open_long_rsi == [20, 23, 26, 29, 32] )
    assert ( Optimize.close_long_rsi == [80, 82, 84, 86, 88, 90] )
    assert ( Optimize.open_short_rsi == [82, 84, 86] )
    assert ( Optimize.close_short_rsi == [20, 23, 26, 29, 32, 35, 38] )
    

def check_trading():
    assert ( Trading.amount == 100_000 )
    assert ( Trading.size == 0.9 )
    assert ( Trading.plong == True )
    assert ( Trading.pshort == True )    

def check_config():
    check_options()
    
    if Options.run:
        check_run()
    
    if Options.optimize:
        check_optim()
        
    check_trading()
    
'''