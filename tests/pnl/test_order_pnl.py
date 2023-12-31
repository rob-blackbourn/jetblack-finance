"""Tests for order P&L"""

from decimal import Decimal
from typing import Union

from jetblack_finance.pnl import (
    FifoOrderPnl,
    LifoOrderPnl,
    BestPriceOrderPnl,
    WorstPriceOrderPnl,
    MatchedOrder,
    IOrder,
)
from jetblack_finance.pnl.scaled_order import ScaledOrder

Number = Union[Decimal, int]


def _to_decimal(number: Number) -> Decimal:
    if isinstance(number, Decimal):
        return number
    return Decimal(number)


class Order(IOrder):
    """A simple order"""

    def __init__(self, quantity: Number, price: Number) -> None:
        self._quantity = _to_decimal(quantity)
        self._price = _to_decimal(price)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    def make_order(self, quantity: Decimal) -> IOrder:
        return Order(quantity, self.price)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Order) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"


def test_long_to_short_with_splits_best_price():
    """long to short, splits, best price"""

    order_pnl = BestPriceOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    buy_6_at_100 = Order(6, 100)
    order_pnl.add(buy_6_at_100)
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl.add(buy_6_at_106)
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl.add(buy_6_at_103)
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl.add(sell_9_at_105)
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -945
    assert order_pnl.realized == 36
    assert order_pnl.avg_cost == 105


def test_long_to_short_with_splits_worst_price():
    """long to short, splits, worst price"""

    order_pnl = WorstPriceOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    buy_6_at_100 = Order(6, 100)
    order_pnl.add(buy_6_at_100)
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl.add(buy_6_at_106)
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl.add(buy_6_at_103)
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl.add(sell_9_at_105)
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -909
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 101


def test_long_to_short_with_splits_fifo():
    """long to short, splits, fifo"""

    order_pnl = FifoOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    buy_6_at_100 = Order(6, 100)
    order_pnl.add(buy_6_at_100)
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl.add(buy_6_at_106)
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl.add(buy_6_at_103)
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl.add(sell_9_at_105)
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -936
    assert order_pnl.realized == 27
    assert order_pnl.avg_cost == 104


def test_long_to_short_with_splits_lifo():
    """long to short, splits, fifo"""

    order_pnl = LifoOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    buy_6_at_100 = Order(6, 100)
    order_pnl.add(buy_6_at_100)
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl.add(buy_6_at_106)
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl.add(buy_6_at_103)
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl.add(sell_9_at_105)
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -918
    assert order_pnl.realized == 9
    assert order_pnl.avg_cost == 102


def test_long_to_short_fifo_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(1, 100))
    order_pnl.add(Order(-1, 102))
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 100)),
            ScaledOrder(Order(-1, 102))
        )
    ]


def test_short_to_long_fifo_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(-1, 102))
    order_pnl.add(Order(1, 100))
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(-1, 102)),
            ScaledOrder(Order(1, 100))
        )
    ]


def test_long_to_short_fifo_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(1, 102))
    order_pnl.add(Order(-1, 100))
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == -2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 102)),
            ScaledOrder(Order(-1, 100))
        )
    ]


def test_short_to_long_fifo_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(-1, 100))
    order_pnl.add(Order(1, 102))
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == -2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(-1, 100)),
            ScaledOrder(Order(1, 102))
        )
    ]


def test_long_sell_fifo_through_flat():

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(1, 101))
    order_pnl.add(Order(-2, 102))
    assert order_pnl.quantity == -1
    assert order_pnl.cost == 102
    assert order_pnl.realized == 1
    assert list(order_pnl.unmatched) == [
        ScaledOrder(Order(-2, 102), -1)
    ]
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 101), 1),
            ScaledOrder(Order(-2, 102), -1)
        )
    ]


def test_short_buy_fifo_through_flat():

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(-1, 102))
    order_pnl.add(Order(2, 101))
    assert order_pnl.quantity == 1
    assert order_pnl.cost == -101
    assert order_pnl.realized == 1
    assert list(order_pnl.unmatched) == [
        ScaledOrder(Order(2, 101), 1)
    ]
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(-1, 102), -1),
            ScaledOrder(Order(2, 101), 1)
        )
    ]


def test_one_buy_many_sells_fifo():

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(10, 101))
    order_pnl.add(Order(-5, 102))
    assert order_pnl.quantity == 5
    assert order_pnl.cost == -505
    assert order_pnl.realized == 5
    order_pnl.add(Order(-5, 104))
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 20
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(10, 101), 5),
            ScaledOrder(Order(-5, 102), -5)
        ),
        MatchedOrder(
            ScaledOrder(Order(10, 101), 5),
            ScaledOrder(Order(-5, 104), -5)
        ),
    ]


def test_pnl():

    order_pnl = FifoOrderPnl()

    # Buy 10 @ 100
    order_pnl.add(Order(10, 100))
    assert order_pnl.pnl_strip(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?
    assert order_pnl.pnl_strip(102) == (10, 100.0, 102, 0, 20)

    # What if we buy another 5 at 102?
    order_pnl.add(Order(10, 102))
    assert order_pnl.pnl_strip(102) == (20, 101.0, 102, 0, 20)

    # What is the P&L if the price goes to 104?
    assert order_pnl.pnl_strip(104) == (20, 101.0, 104, 0, 60)

    # What if we sell 10 at 104?
    order_pnl.add(Order(-10, 104))
    assert order_pnl.pnl_strip(104) == (10, 102.0, 104, 40, 20)

    # What if the price drops to 102?
    assert order_pnl.pnl_strip(102) == (10, 102.0, 102, 40, 0)

    # What if we sell 10 at 102?
    order_pnl.add(Order(-10, 102))
    assert order_pnl.pnl_strip(102) == (0, 0, 102, 40, 0)


def test_many_buys_one_sell_fifo():

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(1, 100))
    order_pnl.add(Order(1, 102))
    order_pnl.add(Order(1, 101))
    order_pnl.add(Order(1, 104))
    order_pnl.add(Order(1, 103))
    order_pnl.add(Order(-5, 104))
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 100), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 102), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 101), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 104), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 103), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
    ]


def test_many_buys_one_sell_lifo():

    order_pnl = LifoOrderPnl()

    order_pnl.add(Order(1, 100))
    order_pnl.add(Order(1, 102))
    order_pnl.add(Order(1, 101))
    order_pnl.add(Order(1, 104))
    order_pnl.add(Order(1, 103))
    order_pnl.add(Order(-5, 104))
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 103), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 104), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 101), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 102), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 100), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
    ]


def test_many_buys_one_sell_best_price():

    order_pnl = BestPriceOrderPnl()

    order_pnl.add(Order(1, 100))
    order_pnl.add(Order(1, 102))
    order_pnl.add(Order(1, 101))
    order_pnl.add(Order(1, 104))
    order_pnl.add(Order(1, 103))
    order_pnl.add(Order(-5, 104))
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 100), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 101), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 102), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 103), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 104), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
    ]


def test_many_sells_one_buy_best_price():

    order_pnl = BestPriceOrderPnl()

    order_pnl.add(Order(-1, 100))
    order_pnl.add(Order(-1, 102))
    order_pnl.add(Order(-1, 101))
    order_pnl.add(Order(-1, 104))
    order_pnl.add(Order(-1, 103))
    order_pnl.add(Order(5, 104))
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(-1, 104), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 103), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 102), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 101), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 100), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
    ]


def test_many_buys_one_sell_worst_price():

    order_pnl = WorstPriceOrderPnl()

    order_pnl.add(Order(1, 100))
    order_pnl.add(Order(1, 102))
    order_pnl.add(Order(1, 101))
    order_pnl.add(Order(1, 104))
    order_pnl.add(Order(1, 103))
    order_pnl.add(Order(-5, 104))
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(1, 104), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 103), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 102), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 101), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
        MatchedOrder(
            ScaledOrder(Order(1, 100), 1),
            ScaledOrder(Order(-5, 104), -1)
        ),
    ]


def test_many_sells_one_buy_worst_price():

    order_pnl = WorstPriceOrderPnl()

    order_pnl.add(Order(-1, 100))
    order_pnl.add(Order(-1, 102))
    order_pnl.add(Order(-1, 101))
    order_pnl.add(Order(-1, 104))
    order_pnl.add(Order(-1, 103))
    order_pnl.add(Order(5, 104))
    assert order_pnl.matched == [
        MatchedOrder(
            ScaledOrder(Order(-1, 100), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 101), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 102), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 103), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
        MatchedOrder(
            ScaledOrder(Order(-1, 104), -1),
            ScaledOrder(Order(5, 104), 1)
        ),
    ]


def test_fraction_quantities():

    order_pnl = FifoOrderPnl()

    order_pnl.add(Order(Decimal("10.17"), Decimal("2.54")))
    order_pnl.add(Order(Decimal("-8.17"), Decimal("2.12")))
    assert order_pnl.quantity == 2
    order_pnl.add(Order(Decimal("-1.5"), Decimal("2.05")))
    assert order_pnl.quantity == Decimal("0.5")
