import backtrader as bt
from backtrader import Strategy
from indicators import BreakoutIndicator

from trading import Signal


#
# logging
#
import logging
logger = logging.getLogger()


def log_signal(level, i, data, signal):
    name = "BUY" if signal == Signal.BUY else "SELL" if signal == Signal.SELL else "NONE"
    logger.log(level, f'{i}, {data.open.array[i]}, {data.high.array[i]}, {data.low.array[i]}, {data.close.array[i]}, {data.volume.array[i]}, {name}')

def log_signals(level, data, signal, s):
    if level < logger.level:
        return

    signals = signal.array
    for i in range(0, len(signals)):
        signal = int(signals[i])
        match(s):
            case Signal.BUY:
                if Signal.BUY == signal:
                    log_signal(level, i, data, signal)

            case Signal.SELL:
                if Signal.SELL == signal:
                    log_signal(level, i, data, signal)

            case Signal.EITHER:
                if signal in [Signal.BUY, Signal.SELL]:
                    log_signal(level, i, data, signal)




class BreakoutStrategy(Strategy):

    LOG_INIT = False
    LOG_ORDERS = False

    LOG_LEVEL = logging.INFO

    LONG = True
    SHORT = False

    VERBOSE = False

    run_nr = 1

    #
    # input parameters for the BreakoutStrategy class
    # these parameters need to be set in the main program and
    # can be used with optimize to get the optimal value combinations
    #
    params = dict(
        ticker      = None,
        tp_sl_ratio = 0.0,
        sl_distance = 0.0,         # distance % below or above current price depending on direction

        #
        # the following parameters will be received from cerebro
        #

        backcandles  = 0,
        gap_window   = 0,
        zone_height  = 0.0,
        breakout_f   = 0.0,

    #    pivot_window = 0,     <= not used now, pivots are calculated outside
        pivots       = [int]
    )


    def log_parameters(self, params):
        logger.debug(f'ticker: {params.ticker}, tp_sl_ratio: {params.tp_sl_ratio}, sl_distance: {params.sl_distance}, backcandles: {params.backcandles}, gap_window: {params.gap_window}, zone_height: {params.zone_height}, breakout_f: {params.breakout_f}')


    #
    # BreakoutStrategy.log
    #
    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        logger.log(BreakoutStrategy.LOG_LEVEL, '%s, %s' % (dt.isoformat(), txt))


    #
    # BreakoutStrategy.__init__
    #
    def __init__(self):


        print(f"calculating signals, run no: {BreakoutStrategy.run_nr}")
        self.log_parameters(self.params)

        # keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None

        #self.ema_signal = is_trend(self.data, backcandles=10)

        #self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=14)#self.params.maperiod)
        #bt.indicators.ExponentialMovingAverage(self.datas, period=25)

        #print(len(self.ema))
        stopfactor = 3.0
        atr = bt.ind.ATR(self.data, period=14)
        emaatr = bt.ind.EMA(atr, period=10)
        self.stop_dist = emaatr * stopfactor

        self.s_ma = bt.indicators.ExponentialMovingAverage(self.data, period=14)
        self.l_ma = bt.indicators.SimpleMovingAverage(self.data, period=50)

        self.sl_dist = self.params.sl_distance     # stop distance as fraction of last close
        self.tp_sl   = self.params.tp_sl_ratio     # w/l ratio


        # get signals and reset signal index
        self.signal = \
            BreakoutIndicator(
                self.data,
                backcandles = self.params.backcandles,
                gap_window  = self.params.gap_window,
                zone_height = self.params.zone_height,
                pivots      = self.params.pivots,
                breakout_f  = self.params.breakout_f
            )


        log_signals(logging.INFO, self.data, self.signal, Signal.BUY|Signal.SELL )


    def accept_short(self) -> bool:
        #print (f'short: {self.data.close[0]} {self.s_ma[0]} {self.l_ma[0]}')
        return BreakoutStrategy.SHORT and self.data.close[0] < self.s_ma[0] and self.s_ma[0] < self.l_ma[0]

    def accept_long(self) -> bool:
        #print (f'long: {self.data.close[0]} {self.s_ma[0]} {self.l_ma[0]}')
        return BreakoutStrategy.LONG and self.data.close[0] > self.s_ma[0] and self.s_ma[0] > self.l_ma[0]


    def start(self):
        BreakoutStrategy.run_nr = BreakoutStrategy.run_nr + 1


    def next(self):
        # log current close
        #self.log(f'Close price: {self.data.close[0]:8.4f}')

        #if len(self.trades) == 1:
        #    for trade in self.trades:
        #        trade.sl = trade.entry_price

        # pending order
        if self.order:
            return

        if not self.position:   # Check if we are in the market
        #if self.open_positions <= MAX_OPEN:
            close = self.data.close[0]           # last close

            match self.signal:

                case Signal.SELL:
                    if self.accept_short():
                        stop1  = close * (1.0 + self.sl_dist)
                        limit1 = close * (1.0 - self.tp_sl * self.sl_dist)

                        self.log(f'OPEN SELL [close={close:6.4f}, stoploss={stop1:6.4f}, limit={limit1:6.4f}]')
                        self.order = self.sell_bracket(limitprice=limit1, stopprice=stop1, size=None)

                case Signal.BUY:
                    if self.accept_long():
                        stop1  = close * (1.0 - self.sl_dist)
                        limit1 = close * (1.0 + self.tp_sl * self.sl_dist)

                        self.log(f'OPEN BUY [close={close:6.4f}, stoploss={stop1:6.4f}, limit={limit1:6.4f}]')
                        self.order = self.buy_bracket(limitprice=limit1, stopprice=stop1, size=None)
                        #self.order = self.buy_bracket(exectype=bt.Order.StopTrail, trailpercent=2*s_fac, limitprice=limit1)
                case 0:
                    pass
                case _:
                    raise ValueError(f'Signal: {self.signal} is invalid. Should be either 0, 1, or 2')

        else:  # we have a current position
            pass

        # incr signal index



    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            return


        # order completed
        if order.status in [order.Completed]:
            # BUY
            if order.isbuy():
                self.log(f'BUY EXECUTED [Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}]')

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

            # SELL
            elif order.issell():
                self.log(f'SELL EXECUTED [Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}]')

            #self.open_positions = self.open_positions +1
            self.bar_executed = len(self)


        elif order.status == order.Canceled:
            self.log('Order Canceled')
        elif order.status == order.Margin:
            self.log('Order Margin')
        elif order.status == order.Rejected:
            self.log('Order Rejected')

        # Write down: no pending order
        self.order = None


    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        #self.open_positions = self.open_positions -2
        if BreakoutStrategy.VERBOSE:
            print(f'{trade.baropen:5d}, {bt.num2date(trade.dtopen)}, {trade.barclose:5d}, {bt.num2date(trade.dtclose)}, {trade.pnl:8.3f}, {trade.pnlcomm:8.3f}')

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:8.3f}, NET {trade.pnlcomm:8.3f}\n******')


