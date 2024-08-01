![知识星球](./zsxq.png)

# bt-qmt-store
Backtrader QMT Store

## 1. 安装
```shell
pip install qmtbt
```
## 2. 使用

```python
import backtrader as bt
from qmtbt import QMTStore

cerebro = bt.Cerebro()

store = QmtStore()

data = store.getdata(dataname='600115.SH', timeframe=bt.TimeFrame.Days, fromdate=datetime(2022, 1, 1), todate=datetime(2023, 9, 6), dividend_type='front')
cerebro.adddata(data)
```

### timeframe
支持以下时间周期：

```python
period_map = {
  bt.TimeFrame.Days: '1d',
  bt.TimeFrame.Minutes: '1m',
  bt.TimeFrame.Ticks: 'tick'
}
```
