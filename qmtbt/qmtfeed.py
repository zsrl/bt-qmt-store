#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import deque
from datetime import datetime
import backtrader as bt
from backtrader.feed import DataBase

from .qmtstore import QMTStore

class MetaQMTFeed(DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaQMTFeed, cls).__init__(name, bases, dct)

        # Register with the store
        QMTStore.DataCls = cls


class QMTFeed(DataBase, metaclass=MetaQMTFeed):
    """
    QMT eXchange Trading Library Data Feed.
    Params:
      - ``historical`` (default: ``False``)
    """

    lines = ('lastClose', 'amount', 'pvolume', 'stockStatus', 'openInt', 'lastSettlementPrice', 'settlementPrice', 'transactionNum', 'askPrice1', 'askPrice2', 'askPrice3', 'askPrice4', 'askPrice5', 'bidPrice1', 'bidPrice2', 'bidPrice3', 'bidPrice4', 'bidPrice5', 'askVol1', 'askVol2', 'askVol3', 'askVol4', 'askVol5', 'bidVol1', 'bidVol2', 'bidVol3', 'bidVol4', 'bidVol5', )

    params = (
        ('live', False),  # only historical download
        ('timeframe', bt.TimeFrame.Ticks)
    )

    def __init__(self, **kwargs):
        self._timeframe = self.p.timeframe
        self._compression = 1
        self.store = kwargs['store']
        self._data = deque()  # data queue for price data
        self._seq = None

    def start(self, ):
        DataBase.start(self)

        period_map = {
            bt.TimeFrame.Days: '1d',
            bt.TimeFrame.Minutes: '1m',
            bt.TimeFrame.Ticks: 'tick'
        } 

        if not self.p.live:
            self._history_data(period=period_map[self.p.timeframe])
            print(f'{self.p.dataname}历史数据装载成功！')
        else:
            self._history_data(period=period_map[self.p.timeframe])
            print(f'{self.p.dataname}实时数据装载成功！')
            # self._live_data(period=period_map[self.p.timeframe])

    def stop(self):
        DataBase.stop(self)

        if self.p.live:
            self.store._unsubscribe_live(self._seq)

    def _load(self):
        while len(self._data):

            current = self._data.popleft()

            for key in current.keys():   
                try: 
                    value = current[key]
                    if key == 'time':
                        dtime = datetime.fromtimestamp(value // 1000)
                        self.lines.datetime[0] = bt.date2num(dtime)
                    elif key == 'lastPrice' and self.p.timeframe == bt.TimeFrame.Ticks:
                        self.lines.close[0] = value
                    else:
                        attr = getattr(self.lines, key)
                        attr[0] = value
                except:
                    pass
            return True
        return None
    
    def haslivedata(self):
        return self.p.live and self._data

    def islive(self):
        return self.p.live
    
    def _format_datetime(self, dt, period='1d'):
        if dt is None:
            return ''
        else:
            if period == '1d':
                formatted_string = dt.strftime("%Y%m%d")
            else:
                formatted_string = dt.strftime("%Y%m%d%H%M%S")
            return formatted_string

    def _append_data(self, item):
        self._data.append(item)    
    
    def _history_data(self, period):

        start_time = self._format_datetime(self.p.fromdate, period)
        end_time = self._format_datetime(self.p.todate, period)

        res = self.store._fetch_history(symbol=self.p.dataname, period=period, start_time=start_time, end_time=end_time)
        result = res.to_dict('records')
        for item in result:
            self._data.append(item)  

    def _live_data(self, period):

        def on_data(res):
            self._data.append(res.iloc[0].to_dict())


        self._seq = self.store._subscribe_live(symbol=self.p.dataname, period=period, callback=on_data)