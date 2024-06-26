# jetblack-finance

Code useful in finance.

## Trading P&L

```python
from jetblack_finance.pnl import FifoOrderPnl, Order

pnl = FifoOrderPnl()

# Buy 10 @ 100
pnl = pnl + Order(10, 100)
# (quantity, avg_cost, price, realized, unrealized)
assert pnl.strip(100) == (10, 100, 100, 0, 0)

# What is the P&L if the price goes to 102? 
assert pnl.strip(102) == (10, 100.0, 102, 0, 20)

# What if we buy another 5 at 102?
pnl. = pnl + Order(10, 102)
assert pnl.strip(102) == (20, 101.0, 102, 0, 20)

# What is the P&L if the price goes to 104?
assert pnl.strip(104) == (20, 101.0, 104, 0, 60)

# What if we sell 10 at 104?
pnl = pnl + Order(-10, 104)
assert pnl.strip(104) == (10, 102.0, 104, 40, 20)

# What if the price drops to 102?
assert pnl.strip(102) == (10, 102.0, 102, 40, 0)

# What if we sell 10 at 102?
pnl = pnl + Order(-10, 102)
assert trading_pnl.pnl(102) == (0, 0, 102, 40, 0)
```

## Order Book

This is a demonstration implementation of an algorithm for a time weighted,
limit order book written in Python.

A limit order is an order that can be filled at a given price.

The orders are "time weighted", in that older orders are executed before newer
orders, where the prices are the same.

The orders support the following styles:

  * `LIMIT` - a simple limit order,
  * `STOP` - a stop order.
  * `KILL_OR_FILL` - a limit order that should either be completely filled, or
    cancelled,
  * `IMMEDIATE_OR_CANCEL` - a limit order which must be either partially filled
    or cancelled,
  * `BOOK_OR_CANCEL` - a limit order which must first go into the book,
    otherwise it must be cancelled.

### Implementation

At the base layer there is an `Order` which holds the `order_id`, `side`,
`price` and `size` of an order.

As multiple orders can be placed at the same price, each price holds an
`AggregateOrder` which contains a queue of all the individual orders. Since the
orders are executed in the sequence in which they were placed (FIFO), new orders
are appended to the back of the queue, while orders to execute are taken from
the front.

The aggregated orders are arranged by price with the `AggregateOrderSide` class.
This arranges the aggregate orders by price ascending, so the best bid is the
last aggregated order, and the best offer is the first aggregated order.

The aggregated order sides are brought together in the `OrderBook` which
presents the client facing functionality. The `OrderBook` is a wrapper for
`OrderBookManager`, which manages the orders and performs *matching* to produce
fills when an order matches or crosses. Crossing is a special case where an
order for a buy (or sell) is made at a higher (or lower) price than the best
offer (or bid).

Finally there is an `ExchangeOrderBook` which maintains the order books
for a given set of tickers.

#### OrderBook / ExchangeOrderBook

The order books have three main methods:

  * `add_limit_order`
  * `amend_limit_order`
  * `cancel_limit_order`

##### add_limit_order(side: Side, price: Decimal, size: int, style: Style) -> Tuple[Optional[int], List[Fill], List[int]]

Adding a limit order produces a tuple of three values:

  * An optional order id if the order could be added,
  * A list of fills that were generated,
  * A list of cancelled orders, if the order generated cancellations.

##### amend_limit_order(self, order_id: int, size: int) -> None:

As the order book is time weighted, only the size of the order can be 
changed, to maintain fair execution.

##### cancel_limit_order(self, order_id: int) -> None

An order may be cancelled.

#### Plugins

In an attempt to keep the core code clean, order styles are implemented as
plugins.

### Usage

The following is taken from the tests.

```python
from decimal import Decimal
from jetblack_finance.order_book import ExchangeOrderBook, Side, Fill, Style

# Create and exchange order book for two tickers.
order_book = ExchangeOrderBook(["AAPL", "MSFT"])

# Build the book.
orders = [
    ('AAPL', Side.BUY, Decimal('134.76'), 10),
    ('MSFT', Side.BUY, Decimal('239.23'), 5),
    ('MSFT', Side.SELL, Decimal('239.28'), 15),
    ('MSFT', Side.SELL, Decimal('239.30'), 2),
    ('AAPL', Side.BUY, Decimal('134.72'), 50),
    ('MSFT', Side.BUY, Decimal('239.14'), 20),
    ('MSFT', Side.BUY, Decimal('239.12'), 25),
    ('MSFT', Side.BUY, Decimal('239.14'), 10),
    ('AAPL', Side.SELL, Decimal('134.79'), 25),
    ('AAPL', Side.SELL, Decimal('135.00'), 40),
    ('AAPL', Side.SELL, Decimal('135.05'), 100),
    ('MSFT', Side.SELL, Decimal('239.32'), 80),
    ('AAPL', Side.SELL, Decimal('135.08'), 50),
    ('AAPL', Side.BUY, Decimal('134.20'), 120),
]
for ticker, side, price, size in orders:
    order_book.add_limit_order(ticker, side, price, size, Style.VANILLA)

assert str(
    order_book.books['AAPL']
) == '134.20x120,134.72x50,134.76x10 : 134.79x25,135.00x40,135.05x100,135.08x50'

assert str(
    order_book.books['MSFT']
) == '239.12x25,239.14x30,239.23x5 : 239.28x15,239.30x2,239.32x80'

# Submit a matching order.
order_id, fills, cancels = order_book.add_limit_order(
    'AAPL',
    Side.BUY,
    Decimal('134.79'),
    20,
    Style.VANILLA
)
assert len(fills) == 1
assert fills == [
    Fill(8, 3, Decimal('134.79'), 20)
]
assert not cancels
```
