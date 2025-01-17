from backtrader import BrokerBase, OrderBase, Order
from backtrader.position import Position
from backtrader.utils.py3 import queue, with_metaclass
import random
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from .qmtstore import QMTStore

class QMTOrder(OrderBase):
    def __init__(self, owner, data, ccxt_order):
        self.owner = owner
        self.data = data
        self.ccxt_order = ccxt_order
        self.executed_fills = []
        self.ordtype = self.Buy if ccxt_order['side'] == 'buy' else self.Sell
        self.size = float(ccxt_order['amount'])

        super(QMTOrder, self).__init__()

class MetaQMTBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaQMTBroker, cls).__init__(name, bases, dct)
        QMTStore.BrokerCls = cls

class QMTBroker(BrokerBase, metaclass=MetaQMTBroker):
    pass

    def __init__(self, **kwargs):

        self.store = QMTStore(**kwargs)
        self.mini_qmt_path = kwargs.get('mini_qmt_path')
        self.account_id = kwargs.get('account_id')

        session_id = int(random.randint(100000, 999999))

        xt_trader = XtQuantTrader(self.mini_qmt_path, session_id)
        # 启动交易对象
        xt_trader.start()
        # 连接客户端
        connect_result = xt_trader.connect()

        if connect_result == 0:
            print('连接成功')

        account = StockAccount(self.account_id)
        # 订阅账号
        res = xt_trader.subscribe(account)

        self.xt_trader = xt_trader
        self.account = account


    def getcash(self):
        res = self.query_stock_asset(self.account)

        self.cash = res.cash

        return self.cash
    
    def getvalue(self, datas=None):

        res = self.query_stock_asset(self.account)

        self.value = res.market_value

        return self.value
    
    def getposition(self, data, clone=True):

        xt_position = self.xt_trader.query_stock_position(self.account, data._dataname)
        pos = Position(size=xt_position.volume, price=xt_position.avg_price)
        return pos
    
    def get_notification(self):
        try:
            return self.notifs.get(False)
        except queue.Empty:
            return None
    
    def notify(self, order):
        self.notifs.put(order)

    def next(self):
        pass

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            **kwargs):
        pass

    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailperc7ent=None,
             **kwargs):
        pass

    def cancel(self, order):
        pass

