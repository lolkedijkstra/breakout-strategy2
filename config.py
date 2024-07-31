import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


class Options:
    save_snapshot: bool = True
    store_signals: bool = True
    store_actions: bool = True
    
    optimize: bool = False
    run: bool = True
    plotting: bool = False

class Trading:
    amount: int = 100_000
    size: float = 0.9
    pshort: bool = False
    plong: bool = True

class Params:   
    backcandles: int = 40
    sl_distance: float = 0.025
    tp_sl_ratio: float = 1.9
    zone_height: float = 0.002
    breakout_factor: float = 1.84
    
    rsi_period: int = 14
    open_long_rsi = 31
    close_long_rsi = 95
    open_short_rsi = 85
    close_short_rsi = 17
        
  
    
   



def make_range_int(fld):
    if len(fld) == 3:
        return range(fld[0], fld[1], fld[2])
    
    return range(fld[0], fld[1])


from array import array
def make_range_float(fld):
    sz = (fld[1] - fld[0])/fld[2]
    values  = [0.0] * sz
    
    values[0] = fld[0]  
    for i in range(1, sz):
        values[i] = values[i-1] + fld[2]
        
    return list(values)


def load_config(config: str) -> None:
    logger.info("load_config: start")

    try:
        with open(config, "r") as conf:
            c = json.load(conf)
            Params.backcandles = c['params']['backcandles']
            Params.sl_distance = c['params']['sl_distance']
            Params.tp_sl_ratio = c['params']['tp_sl_ratio']
            Params.zone_height = c['params']['zone_height']
            Params.breakout_factor = c['params']['breakout_factor']
            
            Params.rsi_period = c['params']['rsi_period']
            
            Params.open_long_rsi = c['params']['open_long_rsi']
            Params.close_long_rsi = c['params']['close_long_rsi']

            Params.open_short_rsi = c['params']['open_short_rsi']
            Params.close_short_rsi = c['params']['close_short_rsi']

            Options.save_snapshot = c['options']['save_snapshot']
            Options.store_signals = c['options']['store_signals']
            Options.store_actions = c['options']['store_actions']
            
            Options.optimize = c['options']['optimize']
            Options.run = c['options']['run']
            Options.plotting = c['options']['plotting']
		
            Trading.amount = c['trading']['amount']
            Trading.size = c['trading']['size']
            Trading.plong = c['trading']['long']
            Trading.pshort = c['trading']['short']
            
            
            if Options.optimize:
                bt_params = c['params'].get('optimize')
                if bt_params:
                    fld = bt_params.get("backcandles")
                    if fld:
                        Params.backcandles = make_range_int(fld)
                    
                    fld = bt_params.get("sl_distance")
                    if fld:
                        Params.sl_distance = make_range_float(fld)
                    
                    fld = bt_params.get('open_long_rsi_range')
                    if fld:
                        Params.open_long_rsi_range = make_range_int(fld)
                        
                    fld = bt_params.get('close_long_rsi_range')
                    if fld:
                        Params.close_long_rsi_range = make_range_int(fld)

                    fld = bt_params.get('open_short_rsi_range')
                    if fld:
                        Params.open_short_rsi_range = make_range_int(fld)
                    
                    fld = bt_params.get('close_short_rsi_range')
                    if fld:
                        Params.close_short_rsi_range = make_range_int(fld)
                    
                    fld = bt_params.get('enter_short_rsi_range')
                    if fld:
                        Params.enter_short_rsi_range = make_range_int(fld)



            
    except Exception as e:
        logger.error(f'\t{e} {config}')
        
        
    logger.info("load_config: end\n")


def print_config():
    print("todo: print_config")
