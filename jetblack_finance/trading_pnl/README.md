# Trading P/L

```python
from jetblack_finance.trading_pnl import TradingPnl, IPnlTrade, add_trade
from jetblack_finance.trading_pnl.impl.simple import (
    MarketTrade,
    MatchedPool,
    UnmatchedPool,
)

matched = MatchedPool()
unmatched = UnmatchedPool.Fifo()
pnl = TradingPnl(Decimal(0), Decimal(0), Decimal(0))

# Buy 10 @ 100
pnl = add_trade(pnl, MarketTrade(10, 100), unmatched, matched)
# (quantity, avg_cost, price, realized, unrealized)
assert pnl.strip(100) == (10, 100, 100, 0, 0)

# What is the P&L if the price goes to 102? 
assert pnl.strip(102) == (10, 100.0, 102, 0, 20)

# What if we buy another 5 at 102?
pnl. = add_trade(pnl, MarketTrade(10, 102), unmatched, matched)
assert pnl.strip(102) == (20, 101.0, 102, 0, 20)

# What is the P&L if the price goes to 104?
assert pnl.strip(104) == (20, 101.0, 104, 0, 60)

# What if we sell 10 at 104?
pnl = add_trade(pnl, MarketTrade(-10, 104), unmatched, matched)
assert pnl.strip(104) == (10, 102.0, 104, 40, 20)

# What if the price drops to 102?
assert pnl.strip(102) == (10, 102.0, 102, 40, 0)

# What if we sell 10 at 102?
pnl = add_trade(pnl, MarketTrade(-10, 102), unmatched, matched)
assert trading_pnl.pnl(102) == (0, 0, 102, 40, 0)
```
