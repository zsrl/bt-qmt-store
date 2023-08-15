from backtrader import BrokerBase, OrderBase, Order
from backtrader.position import Position
from backtrader.utils.py3 import queue, with_metaclass

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

    def getcash(self):

        return self.cash
    
    def getvalue(self, datas=None):

        return self.value
    
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

