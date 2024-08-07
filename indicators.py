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


class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long', 'stop_short',)
    plotinfo = dict(subplot=False, plotlinelabels=True)

    params = dict(
        atrperiod=14,
        emaperiod=10,
        stopfactor=3.0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        # Volatility which determines stop distance
        atr = bt.ind.ATR(self.data, period=self.p.atrperiod)
        emaatr = bt.ind.EMA(atr, period=self.p.emaperiod)
        self.stop_dist = emaatr * self.p.stopfactor

        # Running stop price calc, applied in next according to market pos
        self.s_l = self.data - self.stop_dist
        self.s_s = self.data + self.stop_dist

    def next(self):
        # When entering the market, the stop has to be set
        if self.strat.entering > 0:  # entering long
            self.l.stop_long[0] = self.s_l[0]
        elif self.strat.entering < 0:  # entering short
            self.l.stop_short[0] = self.s_s[0]

        else:  # In the market, adjust stop only in the direction of the trade
            if self.strat.position.size > 0:
                self.l.stop_long[0] = max(self.s_l[0], self.l.stop_long[-1])
            elif self.strat.position.size < 0:
                self.l.stop_short[0] = min(self.s_s[0], self.l.stop_short[-1])

