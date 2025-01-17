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