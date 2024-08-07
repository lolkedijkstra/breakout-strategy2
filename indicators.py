import backtrader as bt

#
# see: https://www.backtrader.com/recipes/indicators/stochrsi/stochrsi/
#
class StochRSI(bt.Indicator):
    lines = ('stochrsi',)
    params = dict(
        period=14,      # to apply to RSI
        pperiod=None,   # if passed apply to HighestN/LowestN, else "period"
    )

    def __init__(self):
        rsi = bt.ind.RSI(self.data, period=self.p.period)

        pperiod = self.p.pperiod or self.p.period
        maxrsi = bt.ind.Highest(rsi, period=pperiod)
        minrsi = bt.ind.Lowest(rsi, period=pperiod)

        self.l.stochrsi = (rsi - minrsi) / (maxrsi - minrsi)


#
# definition of Indicator: wrapper for calculation
#

from algo import algo
from array import array

class BreakoutIndicator(bt.Indicator):
    lines = ('signal',)

    params = dict(
        backcandles = 0,
        
        gap_window  = 0,
        zone_height = 0,
        breakout_f  = 0,
        pivots      = []
    )

    #
    # signal calculation
    #

    def __init__(self):
        sz = self.data.buflen()
        l_signal = array('f', [0] * sz) # internal array is float
        for i in range(0, sz):
            l_signal[i] = algo.calc_signal(
                    data        = self.data,
                    candle_idx  = i,

                    backcandles = self.params.backcandles,
                    gap_window  = self.params.gap_window,
                    pivots      = self.params.pivots,
                    zone_height = self.params.zone_height,
                    breakout_f  = self.params.breakout_f
                    )

        self.lines.signal.array = l_signal
