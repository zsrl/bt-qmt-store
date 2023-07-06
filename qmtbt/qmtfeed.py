#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import deque
from datetime import datetime

import numpy as np

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

    params = (
        ('live', False),  # only historical download
    )

    _store = QMTStore

    # States for the Finite State Machine in _load
    _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)

    # def __init__(self, exchange, symbol, ohlcv_limit=None, config={}, retries=5):
    def __init__(self, **kwargs):
        self.store = self._store(**kwargs)
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
        else:
            pass

    def stop(self):
        DataBase.stop(self)

        if self.p.live:
            self.store._unsubscribe_live(self._seq)


    def _load(self):
        if len(self._data):
            current = self._data.popleft()

            dtime = datetime.fromtimestamp(current[0] // 1000)

            self.lines.datetime[0] = bt.date2num(dtime)
            self.lines.open[0] = current[1]
            self.lines.high[0] = current[2]
            self.lines.low[0] = current[3]
            self.lines.close[0] = current[4]
            self.lines.volume[0] = current[5]
            return True
        return None
    
    def haslivedata(self):
        return self.p.live and self._data

    def islive(self):
        return self.p.live
    
    def _format_datetime(self, dt, period=bt.TimeFrame.Days):
        if dt is None:
            return ''
        else:
            if period == bt.TimeFrame.Days:
                formatted_string = dt.strftime("%Y%m%d")
            else:
                formatted_string = dt.strftime("%Y%m%d%H%M%S")
            return formatted_string
        
    def _history_data(self, period):

        start_time = self._format_datetime(self.p.fromdate)
        end_time = self._format_datetime(self.p.todate)

        res = self.store._fetch_history(symbol=self.p.dataname, period=period, start_time=start_time, end_time=end_time)
        if period != 'tick':
            time = res['time'].iloc[0].values
            open = res['last'].iloc[0].values
            high = res['high'].iloc[0].values
            low = res['low'].iloc[0].values
            close = res['close'].iloc[0].values
            volume = res['volume'].iloc[0].values
        else:
            res_arr = res[self.p.dataname]
            time = [item[0] for item in res_arr]
            open = [item[1] for item in res_arr]
            high = [item[1] for item in res_arr]
            low = [item[1] for item in res_arr]
            close = [item[1] for item in res_arr]
            volume = [item[7] for item in res_arr]

        result = np.column_stack((time, open, high, low, close, volume))
        for item in result:
            self._data.append(item)

    def _live_data(self, period):

        def on_data(datas):
            res = datas[self.p.dataname]

            if period != 'tick':
                self._data.append({
                    'time': res['time'],
                    'open': res['open'],
                    'high': res['high'],
                    'low': res['low'],
                    'close': res['close'],
                    'volume': res['volume'],
                })
            else:
                self._data.append({
                    'time': res['time'],
                    'open': res['lastPrice'],
                    'high': res['lastPrice'],
                    'low': res['lastPrice'],
                    'close': res['lastPrice'],
                    'volume': res['volume'],
                })


        self._seq = self.store._subscribe_live(symbol=self.p.dataname, period=period, callback=on_data)