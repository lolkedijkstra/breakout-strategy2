import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


class _Options:
           
    def __init__(self, json_p=None):
        self.nodes = dict()
        self.jsp = json_p
 
    
    def _check_value(self, tag, value):
        if value is None:
            if self.jsp is None:
                raise Exception("json source is not set or no value is provided")            
            value = self.jsp.get(tag)
            
        if value is None:
            raise ValueError(f"value is None. No tag named: {tag} in json?")
        
        return value 
      
    def get(self, tag):
        return self.nodes.get(tag)
       
    
    def has(self, tag):
        return tag in self.nodes
    

class Options(_Options):      
    def add(self, tag, value=None):
        value = self._check_value(tag, value)  
        
        if not type (value) in (int, float, bool):
            raise ValueError(f"incorrect type in json object '{tag}'; got: {type (value)}, expected one of: 'int', 'float", 'bool')           
                     
        self.nodes[tag] = value



class RuntimeOptions(Options):
    tags = [
        'save_snapshot','store_signals','store_actions','optimize','run','plotting'
    ]        
    
      
       
class RunOptions(Options):
    tags = [
        'pivot_window',
        'gap_window',
        'backcandles',
        
        'sl_distance',
        'tp_sl_ratio',
        'zone_height',
        'breakout_factor'
    ]
           
class TradingOptions(Options):
    tags = [
        'amount', 'commission', 'size', 'long', 'short'
    ]   
         
          
class OptimizeOptions(_Options):
    @staticmethod
    def _is_range(fld):
        # detect if range (3 values, begin, end, step), otherwise its an array
        return len(fld) == 3 and fld[2] < fld[1]
        
    
    @staticmethod
    def _make_array_int(fld):
        if OptimizeOptions._is_range(fld): 
            return list(range(fld[0], fld[1], fld[2]))
        
        return fld

    @staticmethod
    def _make_array_float(fld):
        if OptimizeOptions._is_range(fld): 
            sz = round((fld[1] - fld[0])/fld[2])
            return ( [fld[0] + fld[2] * x for x in range(0, sz)] )
    
        return fld

    
    def __init__(self, json_p=None):
        self.nodes = dict()
        self.jsp = json_p
     
       
    def add_float(self, tag, value = None):
        value = self._check_value(tag, value)    
        if not type (value) == list:
            raise ValueError(f"incorrect type in json object '{tag}', within 'optimize'; got: {type (value)}, expected: 'list'")           
       
        self.nodes[tag] = OptimizeOptions._make_array_float(value)

        
    def add_int(self, tag, value = None):
        value = self._check_value(tag, value) 
        if not type (value) == list:
            raise ValueError(f"incorrect type in json object '{tag}', within 'optimize'; got: {type (value)}, expected: 'list'")           
        self.nodes[tag] = OptimizeOptions._make_array_int(value)

 

class Config:
    def __init__(self, runtime: RuntimeOptions, run: RunOptions, optim: OptimizeOptions, trading: TradingOptions):
        self.runtime = runtime        
        self.run = run
        self.optim = optim
        self.trading = trading
        
   



def load_config(configfile: str) -> Config:
    logger.debug("load_config: start")

    runtime: RuntimeOptions = None
    run: RunOptions = None
    trading: TradingOptions = None
    optim: OptimizeOptions = None
    
    with open(configfile, "r") as fconf:
        c = json.load(fconf)     
            
        if 'runtimeoptions' in c:      
            runtime = RuntimeOptions(c['runtimeoptions'])
            for tag in RuntimeOptions.tags:
                runtime.add(tag)
            
        if 'run' in c:
            run = RunOptions(c['run'])
            for tag in RunOptions.tags:
                run.add(tag)
                
        if 'optimize' in c:
            optim = OptimizeOptions(c.get('optimize'))
            
            optim.add_int('pivot_window')               
            optim.add_int('gap_window')               
            optim.add_int('backcandles')               

            optim.add_float('sl_distance')
            optim.add_float('tp_sl_ratio')
            optim.add_float('zone_height')
            optim.add_float('breakout_factor')
                                    
        if 'trading' in c:
            trading = TradingOptions(c['trading'])
            for tag in TradingOptions.tags:
                trading.add(tag)
               
    logger.debug("load_config: end\n")   
    return Config(runtime=runtime, run=run, optim=optim, trading=trading)  

