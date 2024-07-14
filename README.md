# bt-qmt-store
Backtrader QMT Store

```python
import backtrader as bt

cerebro = bt.Cerebro()

data = store.getdata(dataname='600115.SH', timeframe=bt.TimeFrame.Days, fromdate=datetime(2022, 1, 1), todate=datetime(2023, 9, 6), dividend_type='front')
cerebro.adddata(data)
```
