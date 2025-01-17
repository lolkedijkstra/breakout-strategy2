import config
from pivot import Pivot



class PivotParameters:

    def __init__(self, conf: config.PivotOptions):
        self.window = Pivot.WINDOW

        if conf is None:
            return

        tag = "window"
        if conf.has(tag):
            self.window = conf.get(tag)


# parameters for regular run
class RunParameters:

    # conf: the JSON object, default if None
    def __init__(self, conf: config.RunOptions):
        # defaults

        self.gap_window = Pivot.WINDOW + 1
        self.backcandles = 40

        self.sl_distance = 0.025
        self.tp_sl_ratio = 1.9
        self.zone_height = 0.001
        self.breakout_factor = 1.84


        if conf is None:
            return


        # copy provided parameters
        tag = "gap_window"
        if conf.has(tag):
            self.gap_window =  conf.get(tag)

        tag = "backcandles"
        if conf.has(tag):
            self.backcandles =  conf.get(tag)

        tag = "sl_distance"
        if conf.has(tag):
            self.sl_distance =  conf.get(tag)

        tag = "tp_sl_ratio"
        if conf.has(tag):
            self.tp_sl_ratio =  conf.get(tag)

        tag = "zone_height"
        if conf.has(tag):
            self.zone_height =  conf.get(tag)

        tag = "breakout_factor"
        if conf.has(tag):
            self.breakout_factor = conf.get(tag)



# parameters for optimization run
class OptimizeParameters:

    # conf: the JSON object, default if None
    def __init__(self, conf: config.OptimizeOptions):
        # defaults
        self.gap_window      = [Pivot.WINDOW+1]
        self.backcandles     = [39, 40]
        self.sl_distance     = [0.024 + x/1000 for x in range(0, 3)]
        self.tp_sl_ratio     = [1.5 + x/10 for x in range(0, 5)]
        self.zone_height     = [0.00090, 0.00095, 0.00100]
        self.breakout_factor = [1.84 + x/25 for x in range(0, 5)]


        if conf is None:
            return

        # copy provided parameters
        tag = 'gap_window'
        if conf.has(tag):
            self.gap_window = conf.get(tag)

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



# parameters for trading
class TradingParameters:

    # conf: the JSON object, default if None
    def __init__(self, conf: config.TradingOptions):
        # defaults
        self.amount = 10000.0
        self.size = 0.9
        self.commission = 0.0
        self.plong: bool = True
        self.pshort: bool = False

        if conf is None:
            return

        # copy provided parameters
        tag = "amount"
        if conf.has(tag):
            self.amount = conf.get(tag)

        tag = "size"
        if conf.has(tag):
            self.size = conf.get(tag)

        tag = "commission"
        if conf.has(tag):
            self.commission = conf.get(tag)

        tag = "long"
        if conf.has(tag):
            self.plong = conf.get(tag)

        tag = "short"
        if conf.has(tag):
            self.pshort = conf.get(tag)


# parameters to switch functions OFF | ON
class RuntimeParameters:

    # conf: the JSON object, default if None
    def __init__(self, conf: config.TradingOptions):
        # defaults
        self.SAVE_SNAPSHOT: bool = False
        self.STORE_SIGNALS: bool = False
        self.STORE_ACTIONS: bool = False
        self.OPTIMIZE: bool = False
        self.RUN: bool = False
        self.PLOTTING: bool = False

        if conf is None:
            return

        tag = "save_snapshot"
        if conf.has(tag):
            self.SAVE_SNAPSHOT = conf.get(tag)

        tag = "store_signals"
        if conf.has(tag):
            self.STORE_ACTIONS = conf.get(tag)

        tag = "store_actions"
        if conf.has(tag):
            self.STORE_ACTIONS = conf.get(tag)

        tag = "optimize"
        if conf.has(tag):
            self.OPTIMIZE = conf.get(tag)

        tag = "run"
        if conf.has(tag):
            self.RUN = conf.get(tag)

        tag = "plotting"
        if conf.has(tag):
            self.PLOTTING = conf.get(tag)


