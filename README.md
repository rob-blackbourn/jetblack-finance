# jetblack-finance

Code useful in finance.

## Trading P&L

```python
from jetblack_finance.pnl import TradingPnl, MatchedTrade, Trade, MatchStyle

trading_pnl = TradingPnl(MatchStyle.FIFO)

# Buy 10 @ 100
trading_pnl.add(10, 100)
assert trading_pnl.pnl(100) == (10, 100, 100, 0, 0)

# What is the P&L if the price goes to 102? 
assert trading_pnl.pnl(102) == (10, 100.0, 102, 0, 20) # (quantity, avg_cost, price, realized, unrealized)

# What if we buy another 5 at 102?
trading_pnl.add(10, 102)
assert trading_pnl.pnl(102) == (20, 101.0, 102, 0, 20)

# What is the P&L if the price goes to 104?
assert trading_pnl.pnl(104) == (20, 101.0, 104, 0, 60)

# What if we sell 10 at 104?
trading_pnl.add(-10, 104)
assert trading_pnl.pnl(104) == (10, 102.0, 104, 40, 20)

# What if the price drops to 102?
assert trading_pnl.pnl(102) == (10, 102.0, 102, 40, 0)

# What if we sell 10 at 102?
trading_pnl.add(-10, 102)
assert trading_pnl.pnl(102) == (0, 0, 102, 40, 0)

```
