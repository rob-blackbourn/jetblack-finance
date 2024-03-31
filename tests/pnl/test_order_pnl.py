"""Tests for order P&L"""

from decimal import Decimal

from jetblack_finance.pnl import (
    FifoOrderPnl,
    LifoOrderPnl,
    BestPriceOrderPnl,
    WorstPriceOrderPnl,
)
from jetblack_finance.pnl.order_pnl.order_pnl_state import MatchedOrder
from jetblack_finance.pnl.order_pnl.split_order import SplitOrder


from .utils import Order


def test_long_to_short_with_splits_best_price():
    """long to short, splits, best price"""

    order_pnl = BestPriceOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    buy_6_at_100 = Order(6, 100)
    order_pnl = order_pnl + buy_6_at_100
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl = order_pnl + buy_6_at_106
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl = order_pnl + buy_6_at_103
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl = order_pnl + sell_9_at_105
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -945
    assert order_pnl.realized == 36
    assert order_pnl.avg_cost == 105

    sell_9_at_107 = Order(-9, 107)
    order_pnl = order_pnl + sell_9_at_107
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 54
    assert order_pnl.avg_cost == 0


def test_long_to_short_with_splits_best_price_with_sub():
    """long to short, splits, best price"""

    order_pnl = BestPriceOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    order_pnl = order_pnl + Order(6, 100)
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    order_pnl = order_pnl + Order(6, 106)
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    order_pnl = order_pnl + Order(6, 103)
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    order_pnl = order_pnl - Order(9, 105)
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -945
    assert order_pnl.realized == 36
    assert order_pnl.avg_cost == 105

    order_pnl = order_pnl - Order(9, 107)
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 54
    assert order_pnl.avg_cost == 0


def test_long_to_short_with_splits_worst_price():
    """long to short, splits, worst price"""

    order_pnl = WorstPriceOrderPnl()

    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 0

    buy_6_at_100 = Order(6, 100)
    order_pnl = order_pnl + buy_6_at_100
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl = order_pnl + buy_6_at_106
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl = order_pnl + buy_6_at_103
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl = order_pnl + sell_9_at_105
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
    order_pnl = order_pnl + buy_6_at_100
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl = order_pnl + buy_6_at_106
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl = order_pnl + buy_6_at_103
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl = order_pnl + sell_9_at_105
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
    order_pnl = order_pnl + buy_6_at_100
    assert order_pnl.quantity == 6
    assert order_pnl.cost == -600
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 100

    buy_6_at_106 = Order(6, 106)
    order_pnl = order_pnl + buy_6_at_106
    assert order_pnl.quantity == 12
    assert order_pnl.cost == -1236
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    buy_6_at_103 = Order(6, 103)
    order_pnl = order_pnl + buy_6_at_103
    assert order_pnl.quantity == 18
    assert order_pnl.cost == -1854
    assert order_pnl.realized == 0
    assert order_pnl.avg_cost == 103

    sell_9_at_105 = Order(-9, 105)
    order_pnl = order_pnl + sell_9_at_105
    assert order_pnl.quantity == 9
    assert order_pnl.cost == -918
    assert order_pnl.realized == 9
    assert order_pnl.avg_cost == 102


def test_long_to_short_fifo_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(1, 100)
    order_pnl = order_pnl + Order(-1, 102)
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 100)),
            SplitOrder(Order(-1, 102))
        )
    ]


def test_short_to_long_fifo_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(-1, 102)
    order_pnl = order_pnl + Order(1, 100)
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(-1, 102)),
            SplitOrder(Order(1, 100))
        )
    ]


def test_long_to_short_fifo_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(1, 102)
    order_pnl = order_pnl + Order(-1, 100)
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == -2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 102)),
            SplitOrder(Order(-1, 100))
        )
    ]


def test_short_to_long_fifo_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(-1, 100)
    order_pnl = order_pnl + Order(1, 102)
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == -2
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(-1, 100)),
            SplitOrder(Order(1, 102))
        )
    ]


def test_long_sell_fifo_through_flat():

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(1, 101)
    order_pnl = order_pnl + Order(-2, 102)
    assert order_pnl.quantity == -1
    assert order_pnl.cost == 102
    assert order_pnl.realized == 1
    assert list(order_pnl.unmatched) == [
        SplitOrder(Order(-2, 102), -1, 1)
    ]
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 101), 0, 1),
            SplitOrder(Order(-2, 102), -1, 1)
        )
    ]


def test_short_buy_fifo_through_flat():

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(-1, 102)
    order_pnl = order_pnl + Order(2, 101)
    assert order_pnl.quantity == 1
    assert order_pnl.cost == -101
    assert order_pnl.realized == 1
    assert list(order_pnl.unmatched) == [
        SplitOrder(Order(2, 101), 1, 1)
    ]
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(-1, 102), 0, 1),
            SplitOrder(Order(2, 101), 1, 1)
        )
    ]


def test_one_buy_many_sells_fifo():

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(10, 101)
    order_pnl = order_pnl + Order(-5, 102)
    assert order_pnl.quantity == 5
    assert order_pnl.cost == -505
    assert order_pnl.realized == 5
    order_pnl = order_pnl + Order(-5, 104)
    assert order_pnl.quantity == 0
    assert order_pnl.cost == 0
    assert order_pnl.realized == 20
    assert len(order_pnl.unmatched) == 0
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(10, 101), 5, 1),
            SplitOrder(Order(-5, 102), 0, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(10, 101), 5, 1),
            SplitOrder(Order(-5, 104), 0, 1)
        ),
    ]


def test_pnl():

    order_pnl = FifoOrderPnl()

    # Buy 10 @ 100
    order_pnl = order_pnl + Order(10, 100)
    assert order_pnl.strip(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?
    assert order_pnl.strip(102) == (10, 100.0, 102, 0, 20)

    # What if we buy another 5 at 102?
    order_pnl = order_pnl + Order(10, 102)
    assert order_pnl.strip(102) == (20, 101.0, 102, 0, 20)

    # What is the P&L if the price goes to 104?
    assert order_pnl.strip(104) == (20, 101.0, 104, 0, 60)

    # What if we sell 10 at 104?
    order_pnl = order_pnl + Order(-10, 104)
    assert order_pnl.strip(104) == (10, 102.0, 104, 40, 20)

    # What if the price drops to 102?
    assert order_pnl.strip(102) == (10, 102.0, 102, 40, 0)

    # What if we sell 10 at 102?
    order_pnl = order_pnl + Order(-10, 102)
    assert order_pnl.strip(102) == (0, 0, 102, 40, 0)


def test_many_buys_one_sell_fifo():

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(1, 100)
    order_pnl = order_pnl + Order(1, 102)
    order_pnl = order_pnl + Order(1, 101)
    order_pnl = order_pnl + Order(1, 104)
    order_pnl = order_pnl + Order(1, 103)
    order_pnl = order_pnl + Order(-5, 104)
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 100), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 102), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 101), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 104), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 103), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
    ]


def test_many_buys_one_sell_lifo():

    order_pnl = LifoOrderPnl()

    order_pnl = order_pnl + Order(1, 100)
    order_pnl = order_pnl + Order(1, 102)
    order_pnl = order_pnl + Order(1, 101)
    order_pnl = order_pnl + Order(1, 104)
    order_pnl = order_pnl + Order(1, 103)
    order_pnl = order_pnl + Order(-5, 104)
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 103), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 104), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 101), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 102), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 100), 0, 1),
            SplitOrder(Order(-5, 104), -4, 1)
        ),
    ]


def test_many_buys_one_sell_best_price():

    order_pnl = BestPriceOrderPnl()

    order_pnl = order_pnl + Order(1, 100)
    order_pnl = order_pnl + Order(1, 102)
    order_pnl = order_pnl + Order(1, 101)
    order_pnl = order_pnl + Order(1, 104)
    order_pnl = order_pnl + Order(1, 103)
    order_pnl = order_pnl + Order(-5, 104)
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 100), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 101), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 102), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 103), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 104), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
    ]


def test_many_sells_one_buy_best_price():

    order_pnl = BestPriceOrderPnl()

    order_pnl = order_pnl + Order(-1, 100)
    order_pnl = order_pnl + Order(-1, 102)
    order_pnl = order_pnl + Order(-1, 101)
    order_pnl = order_pnl + Order(-1, 104)
    order_pnl = order_pnl + Order(-1, 103)
    order_pnl = order_pnl + Order(5, 104)
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(-1, 104), 0, 1),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 103), 0, 1),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 102), 0, 1),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 101), 0, 1),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 100), 0, 1),
            SplitOrder(Order(5, 104), 4)
        ),
    ]


def test_many_buys_one_sell_worst_price():

    order_pnl = WorstPriceOrderPnl()

    order_pnl = order_pnl + Order(1, 100)
    order_pnl = order_pnl + Order(1, 102)
    order_pnl = order_pnl + Order(1, 101)
    order_pnl = order_pnl + Order(1, 104)
    order_pnl = order_pnl + Order(1, 103)
    order_pnl = order_pnl + Order(-5, 104)
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(1, 104), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 103), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 102), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 101), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
        MatchedOrder(
            SplitOrder(Order(1, 100), 0),
            SplitOrder(Order(-5, 104), -4)
        ),
    ]


def test_many_sells_one_buy_worst_price():

    order_pnl = WorstPriceOrderPnl()

    order_pnl = order_pnl + Order(-1, 100)
    order_pnl = order_pnl + Order(-1, 102)
    order_pnl = order_pnl + Order(-1, 101)
    order_pnl = order_pnl + Order(-1, 104)
    order_pnl = order_pnl + Order(-1, 103)
    order_pnl = order_pnl + Order(5, 104)
    assert order_pnl.matched == [
        MatchedOrder(
            SplitOrder(Order(-1, 100), 0),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 101), 0),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 102), 0),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 103), 0),
            SplitOrder(Order(5, 104), 4)
        ),
        MatchedOrder(
            SplitOrder(Order(-1, 104), 0),
            SplitOrder(Order(5, 104), 4)
        ),
    ]


def test_fraction_quantities():

    order_pnl = FifoOrderPnl()

    order_pnl = order_pnl + Order(Decimal("10.17"), Decimal("2.54"))
    order_pnl = order_pnl + Order(Decimal("-8.17"), Decimal("2.12"))
    assert order_pnl.quantity == 2
    order_pnl = order_pnl + Order(Decimal("-1.5"), Decimal("2.05"))
    assert order_pnl.quantity == Decimal("0.5")
