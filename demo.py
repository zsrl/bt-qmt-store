import backtrader as bt
from qmtbt import QMTStore
from datetime import datetime
from xtquant import xtdata
import math

class BuyCondition(bt.Indicator):
    '''买入条件'''
    lines = ('buy_signal',)

    params = (
        ('up_days', 10),  # 连续上涨的天数
    )

    def __init__(self):
        self.lines.buy_signal = bt.If(self.data.close > self.data.close(-250), 1, 0)

    def next(self):
        # 检查250线斜率是否恰好连续向上self.params.up_days个交易日，再往前一个交易日斜率下降
        if len(self) >= self.params.up_days + 1:
            slope_up = all(self.data.close[-i] > self.data.close[-i-1] for i in range(1, self.params.up_days + 1))
            slope_down_before = self.data.close[-self.params.up_days - 1] < self.data.close[-self.params.up_days - 2]
            if slope_up and slope_down_before:
                self.lines.buy_signal[0] = 1
            else:
                self.lines.buy_signal[0] = 0

class SellCondition(bt.Indicator):
    '''卖出条件'''
    lines = ('sell_signal',)

    params = (
        ('hold_days', 20),  # 持有天数
    )

    def __init__(self):
        self.hold_days = 0

    def next(self):
        # 持有self.params.hold_days个交易日卖出
        if self.hold_days >= self.params.hold_days:
            self.lines.sell_signal[0] = 1
            self.hold_days = 0
        else:
            self.lines.sell_signal[0] = 0
            self.hold_days += 1

class Sizer(bt.Sizer):
    '''仓位控制'''
    params = (
        ('buy_count', 1),   # 最大持仓股票个数
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            # 如果是买入，平均分配仓位
            commission_rate = comminfo.p.commission
            size = math.floor(cash * (1 - commission_rate) / data.close[0] / self.params.buy_count / 100) * 100
        else:
            # 如果是卖出，全部卖出
            position = self.broker.getposition(data)
            size = position.size

        return size

class DemoStrategy(bt.Strategy):
    params = (
        ('max_positions', 5),   # 最大持仓股票个数
        ('up_days', 10),        # 连续上涨的天数
        ('hold_days', 20),      # 持有天数
    )

    def log(self, txt, dt=None):
        """ 记录交易日志 """
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 初始化函数
        self.sizer = Sizer()
        self.buy_condition = {d: BuyCondition(d, up_days=self.params.up_days) for d in self.datas}
        self.sell_condition = {d: SellCondition(d, hold_days=self.params.hold_days) for d in self.datas}

    def next(self):
        # 先收集所有需要买入和卖出的股票
        buy_list = []
        sell_list = []

        for i, d in enumerate(self.datas):
            pos = self.getposition(d).size

            if pos and self.sell_condition[d].lines.sell_signal[0] > 0:
                sell_list.append(d)

            if self.buy_condition[d].lines.buy_signal[0] > 0:
                buy_list.append(d)

        # 动态设置Sizer的buy_count参数
        self.sizer.params.buy_count = len(buy_list)

        # 先执行卖出操作
        for d in sell_list:
            self.sell(data=d)

        # 再执行买入操作
        for d in buy_list:
            self.buy(data=d)
        
if __name__ == '__main__':
    

    store = QMTStore()

    code_list = xtdata.get_stock_list_in_sector('沪深300')

    # 添加数据
    datas = store.getdatas(code_list=code_list, timeframe=bt.TimeFrame.Days, fromdate=datetime(2022, 7, 1))

    for d in datas:
        # print(len(d))
        cerebro = bt.Cerebro(maxcpus=16)

        cerebro.adddata(d)

        # 添加策略
        # buy_date = datetime(2022, 8, 1).date()  # 设置固定买入日期
        cerebro.addstrategy(DemoStrategy)

        # cerebro.optstrategy

        # # 设置初始资金
        cerebro.broker.setcash(1000000.0)

        # 设置佣金
        cerebro.broker.setcommission(commission=0.001)

        # 运行回测
        # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.run()
        if cerebro.broker.getvalue() != 1000000.0:
            print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # data.test(1)
    # data.test(2)
    # data.test(3)
    # data.test(4)
    # xtdata.run()

    # 绘制结果
    # cerebro.plot()