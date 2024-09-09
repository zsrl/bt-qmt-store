import backtrader as bt
from qmtbt import QMTStore
from datetime import datetime

store = QMTStore()

class DualMovingAverageStrategy(bt.Strategy):
    params = (
        ('short_window', 10),
        ('long_window', 30),
    )

    def __init__(self):
        self.short_ma = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.params.short_window
        )
        self.long_ma = bt.indicators.MovingAverageSimple(
            self.data.close, period=self.params.long_window
        )

    def next(self):
        print('next', len(self.data.close))
        if self.short_ma > self.long_ma:
            if not self.position:
                self.buy()
        elif self.short_ma < self.long_ma:
            if self.position:
                self.sell()

    def notify_data(self, data, status, *args, **kwargs):
        print(self.data.close[0], 'self.data.close')
        # if status == bt.dataseries.DATASERIES_EVENT_UPDATE:
            # 数据更新事件触发时执行的逻辑
        # print(data)

if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 添加数据
    datas = store.getdatas(code_list=['600519.SH', '600000.SH'], timeframe=bt.TimeFrame.Days, fromdate=datetime(2022, 7, 1))

    store.setdatas(datas)


    # 添加策略
    cerebro.addstrategy(DualMovingAverageStrategy)

    cerebro.optstrategy

    # 设置初始资金
    cerebro.broker.setcash(100000.0)

    # 设置佣金
    cerebro.broker.setcommission(commission=0.001)

    # 运行回测
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # data.test(1)
    # data.test(2)
    # data.test(3)
    # data.test(4)
    # xtdata.run()

    # 绘制结果
    # cerebro.plot()