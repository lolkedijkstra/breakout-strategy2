import backtrader as bt

class PercentRiskSizer(bt.Sizer):
    '''Sizer modeling the Percentage Risk sizing model of Van K. Tharp'''
    params = dict(percrisk=0.01)  # 1% percentage risk

    def _getsizing(self, comminfo, cash, data, isbuy):
        # Risk per 1 contract
        risk = comminfo.p.mult * self.strategy.stoptrailer.stop_dist[0]
        # % of account value to risk
        torisk = self.broker.get_value() * self.p.percrisk
        return torisk // risk  # size to risk
