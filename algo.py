import logging
logger = logging.getLogger()

import statistics
from trading import Signal
from pivot import Pivot


from backtrader import lineseries

class algo:

    @staticmethod
    def is_trend(close:list[float], open:list[float], ema:list[float], backcandles:int=10) -> list[int]:
        ema_signal = [0]*len(close)

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
    def slice(data: lineseries, b: int, e: int):
        return data.get(ago=e-data.buflen(), size=e-b)


    @staticmethod
    def get_pivots(highlow: int, data: list[float], pivots: list[int]) -> list[float]:
        values = []
        for i in range(0, len(data)):
            if pivots[i] == highlow:
                values.append(data[i])

        return values

    @staticmethod
    def get_pivots_high(data: list[float], pivots: list[int]) -> list[float]:
        return algo.get_pivots(Pivot.HIGH, data, pivots)

    @staticmethod
    def get_pivots_low(data: list[float], pivots: list[int]) -> list[float]:
        return algo.get_pivots(Pivot.LOW, data, pivots)


    import typing
    @staticmethod
    def _check_breakout(f_breakout_test: typing.Callable[[float, float, float], int], values: list[float], zone_height: float, cclose: float) -> int:

        # helper function: check if pivots form a zone
        #def _is_zone(values , mean, height):
        def _is_zone(values: list[float], mean: float, zheight: float):
            for value in values:
#                if abs(value-mean) > zheight:
                if abs(value-mean) > zheight * mean:
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
    # zone_height   the RELATIVE price fluctuation
    #
    #from backtrader.feed import Database

    @staticmethod
    def calc_breakout_signal(data, candle_idx: int, backcandles: int, gap_window: int, pivots: list[int], zone_height: float, breakout_f: float) -> int:
        #print( backcandles, gap_window, zone_height)

        # gap_window must be >= pivot window to avoid look ahead bias
        begin = candle_idx - backcandles - gap_window
        end   = candle_idx - gap_window

        if begin < 0 or candle_idx + gap_window >= data.buflen():
            return 0


        _F = breakout_f     # breakout factor
        _N = 3              # number of bounces
        sig = Signal.NONE

        cclose = data.close.array[candle_idx]

        lows = data.low.array
        pvts = algo.get_pivots_low(data=lows[begin:end], pivots=pivots[begin:end])[-_N:]

        if _N == len(pvts):
            sig = algo._check_breakout(
#                    lambda mean, cclose, zheight: (Signal.SELL if (mean - cclose) > zheight * _F else 0),
                    lambda mean, cclose, zheight: (Signal.SELL if (mean - cclose) > zheight * mean * _F else 0),
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
#                lambda mean, cclose, zheight: (Signal.BUY if (cclose - mean) > zheight  * _F else 0),
                lambda mean, cclose, zheight: (Signal.BUY if (cclose - mean) > zheight * mean * _F else 0),
                pvts,
                zone_height,
                cclose
            )

            #if sig != Signal.NONE:
            #    print(f"BUY SIGNAL: {candle_idx}")


        return sig
