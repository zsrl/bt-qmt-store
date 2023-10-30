import random
import sys
import importlib.util

import backtrader as bt
from backtrader.metabase import MetaParams

import pandas as pd


class MetaSingleton(MetaParams):
    '''Metaclass to make a metaclassed class a singleton'''

    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class QMTStore(object, metaclass=MetaSingleton):
    
    def getdata(self, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        kwargs['store'] = self
        qmtFeed = self.__class__.DataCls(*args, **kwargs)
        self.code_list.append({
            **kwargs,
            'feed': qmtFeed
        })
        return qmtFeed

    def getbroker(self, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return self.__class__.BrokerCls(*args, **kwargs)
    
    def __init__(self, mini_qmt_path, xtquant_path, account):

        self.mini_qmt_path = mini_qmt_path
        self.xtquant_path = xtquant_path
        self.account = account
        self.code_list = []
        self.last_tick = None

        # 创建模块spec
        spec = importlib.util.spec_from_file_location('xtquant', f'{self.xtquant_path}\__init__.py')

        # 创建模块实例
        module = importlib.util.module_from_spec(spec)

        # 加载模块到当前Python环境
        spec.loader.exec_module(module)

        sys.modules['xtquant'] = module

        from xtquant import xtdata, xttrader, xttype
        
        self.xtdata = xtdata
        self.xttrader = xttrader
        self.xttype = xttype
        self.xt_trader = None
    
    def connect(self):

        session_id = int(random.randint(100000, 999999))
        xt_trader = self.xttrader.XtQuantTrader(self.mini_qmt_path, session_id)

        xt_trader.start()

        connect_result = xt_trader.connect()

        if connect_result == 0:
            print('连接成功')

            self.stock_account = self.xttype.StockAccount(self.account)

            xt_trader.subscribe(self.stock_account)

            self.xt_trader = xt_trader

    def _auto_expand_array_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Write by ChatGPT4

        Automatically identify and expand DataFrame columns containing array values.

        Returns:
        - A new DataFrame with the expanded columns.
        """
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (list, tuple))).all():
                # Expand the array column into a new DataFrame
                expanded_df = df[col].apply(pd.Series)
                # Generate new column names
                expanded_df.columns = [f"{col}{i+1}" for i in range(expanded_df.shape[1])]
                # Drop the original column and join the expanded columns
                df = df.drop(col, axis=1).join(expanded_df)
        return df

    def _fetch_history(self, symbol, period, start_time='', end_time='', count=-1, dividend_type='none', download=True):
        """
        获取历史数据
        
        参数：
            symbol: 标的代码
            period: 周期
            start_time: 起始日期
            end_time: 终止日期

        """
        if download:
            self.xtdata.download_history_data(stock_code=symbol, period=period, start_time=start_time, end_time=end_time)
        res = self.xtdata.get_local_data(stock_list=[symbol], period=period, start_time=start_time, end_time=end_time, count=count, dividend_type=dividend_type)
        res = res[symbol]
        if period == 'tick':
            res = self._auto_expand_array_columns(res)
        return res
    
    def subscribe_live(self):

        def on_data(datas):
             for item in self.code_list:
                 data = datas[item['dataname']]
                #  if data is not None:
                    #  print(data, 'data')
                    #  item.feed._append_data(data)
             self.last_tick = datas
            # callback(datas)

        return self.xtdata.subscribe_whole_quote(code_list=[item['dataname'] for item in self.code_list], callback=on_data)
    
    def unsubscribe_live(self, seq):
        self.xtdata.unsubscribe_quote(seq)
