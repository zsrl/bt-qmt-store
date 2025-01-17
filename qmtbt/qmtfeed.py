#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import deque
import datetime
import backtrader as bt
from backtrader.feed import DataBase
import time
import threading
import random

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

    lines = ('lastClose', 'amount', 'pvolume', 'stockStatus', 'openInt', 'lastSettlementPrice', 'settlementPrice', 'transactionNum', 'askPrice1', 'askPrice2', 'askPrice3', 'askPrice4', 'askPrice5', 'bidPrice1', 'bidPrice2', 'bidPrice3', 'bidPrice4', 'bidPrice5', 'askVol1', 'askVol2', 'askVol3', 'askVol4', 'askVol5', 'bidVol1', 'bidVol2', 'bidVol3', 'bidVol4', 'bidVol5', 'openInterest', 'dr', 'totaldr', 'preClose', 'suspendFlag', 'settelementPrice', 'pe' )

    params = (
        ('live', False),  # only historical download
        ('timeframe', bt.TimeFrame.Ticks)
    )

    def __init__(self, **kwargs):
        self._timeframe = self.p.timeframe
        self._compression = 1
        self.store = kwargs['store']
        # self.cerebro = kwargs['cerebro']
        self._data = deque()  # data queue for price data
        self._seq = None

    # def __len__(self):
    #     return len(self._data)

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
            self._live_data(period=period_map[self.p.timeframe])
            print(f'{self.p.dataname}实时数据装载成功！')

    def stop(self):
        DataBase.stop(self)

        if self.p.live:
            self.store._unsubscribe_live(self._seq)

    def _get_datetime(self, value):
        dtime = datetime.datetime.fromtimestamp(value // 1000)
        return bt.date2num(dtime)

    def _load_current(self, current):
        for key in current.keys():   
                try: 
                    value = current[key]
                    if key == 'time':
                        self.lines.datetime[0] = self._get_datetime(value)
                    elif key == 'lastPrice' and self.p.timeframe == bt.TimeFrame.Ticks:
                        self.lines.close[0] = value
                    else:
                        attr = getattr(self.lines, key)
                        attr[0] = value
                except Exception as e:
                    print(e)
                    pass
        # print(current, 'current')
        self.put_notification(int(random.randint(100000, 999999)))

    def _load(self, replace=False):
        if len(self._data) > 0:

            current = self._data.popleft()

            self._load_current(current)

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
            if item.get('close') != 0 and item.get('lastPrice') != 0:
                self._data.append(item)

    def _live_data(self, period):

        start_time = self._format_datetime(self.p.fromdate, period)

        def on_data(res):
            print(self.lines.datetime)
            # current = res[self.p.dataname][0]
            # if self._get_datetime(current['time']) == self.lines.datetime[0]:
            #     self._load_current(current)
            # else:
            #     self._data.append(current)


        self._seq = self.store._subscribe_live(symbol=self.p.dataname, period=period, start_time=start_time, callback=on_data)

        res = self.store._fetch_history(symbol=self.p.dataname, period=period, start_time=start_time, download=False)
        result = res.to_dict('records')
        for item in result:
            self._data.append(item)

    # def test(self, close):
    #     # 获取当前日期
    #     current_date = datetime.datetime.now().date()

    #     # 将当前日期转换为datetime对象，并将时间设置为00:00:00
    #     start_of_day = datetime.datetime.combine(current_date, datetime.time.min)

    #     # 将开始时间转换为Unix时间戳（以毫秒为单位）
    #     start_of_day_unix_ms = int(start_of_day.timestamp() * 1000)
    #     current = {
    #         'time': start_of_day_unix_ms,
    #         'close': close,
    #         'open': 1.0,
    #         'high': 1.0,
    #         'low': 1.0,
    #         'volume': 1.0,
    #     }
    #     self._load_current(current)

    # # 定义一个函数，这个函数将在每次循环中执行
    # def my_function():
    #     while True:
    #         self.test(1)
    #         time.sleep(3)  # 暂停3秒

    # # 创建并启动线程
    # thread = threading.Thread(target=my_function)
    # thread.daemon = True  # 设置为守护线程，这样主线程结束时，子线程也会结束
    # thread.start()

