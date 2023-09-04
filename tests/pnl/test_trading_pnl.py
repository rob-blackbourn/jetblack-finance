"""Tests for trading P&L"""

from decimal import Decimal
from typing import Union

from jetblack_finance.pnl import (
    FifoTradingPnl,
    LifoTradingPnl,
    BestPriceTradingPnl,
    WorstPriceTradingPnl,
    MatchedTrade,
    ITrade,
)
from jetblack_finance.pnl.types import ScaledTrade

Number = Union[Decimal, int]


def _to_decimal(number: Number) -> Decimal:
    if isinstance(number, Decimal):
        return number
    return Decimal(number)


class Trade(ITrade):
    """A simple trade"""

    def __init__(self, quantity: Number, price: Number) -> None:
        self._quantity = _to_decimal(quantity)
        self._price = _to_decimal(price)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    def make_trade(self, quantity: Decimal) -> ITrade:
        return Trade(quantity, self.price)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Trade) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"
        # return f"Trade(quantity={self.quantity},price={self.price})"


def test_long_to_short_with_splits_best_price():
    """long to short, splits, best price"""

    trading_pnl = BestPriceTradingPnl()

    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 0

    buy_6_at_100 = Trade(6, 100)
    trading_pnl.add(buy_6_at_100)
    assert trading_pnl.quantity == 6
    assert trading_pnl.cost == -600
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 100

    buy_6_at_106 = Trade(6, 106)
    trading_pnl.add(buy_6_at_106)
    assert trading_pnl.quantity == 12
    assert trading_pnl.cost == -1236
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    buy_6_at_103 = Trade(6, 103)
    trading_pnl.add(buy_6_at_103)
    assert trading_pnl.quantity == 18
    assert trading_pnl.cost == -1854
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    sell_9_at_105 = Trade(-9, 105)
    trading_pnl.add(sell_9_at_105)
    assert trading_pnl.quantity == 9
    assert trading_pnl.cost == -945
    assert trading_pnl.realized == 36
    assert trading_pnl.avg_cost == 105


def test_long_to_short_with_splits_worst_price():
    """long to short, splits, worst price"""

    trading_pnl = WorstPriceTradingPnl()

    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 0

    buy_6_at_100 = Trade(6, 100)
    trading_pnl.add(buy_6_at_100)
    assert trading_pnl.quantity == 6
    assert trading_pnl.cost == -600
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 100

    buy_6_at_106 = Trade(6, 106)
    trading_pnl.add(buy_6_at_106)
    assert trading_pnl.quantity == 12
    assert trading_pnl.cost == -1236
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    buy_6_at_103 = Trade(6, 103)
    trading_pnl.add(buy_6_at_103)
    assert trading_pnl.quantity == 18
    assert trading_pnl.cost == -1854
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    sell_9_at_105 = Trade(-9, 105)
    trading_pnl.add(sell_9_at_105)
    assert trading_pnl.quantity == 9
    assert trading_pnl.cost == -909
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 101


def test_long_to_short_with_splits_fifo():
    """long to short, splits, fifo"""

    trading_pnl = FifoTradingPnl()

    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 0

    buy_6_at_100 = Trade(6, 100)
    trading_pnl.add(buy_6_at_100)
    assert trading_pnl.quantity == 6
    assert trading_pnl.cost == -600
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 100

    buy_6_at_106 = Trade(6, 106)
    trading_pnl.add(buy_6_at_106)
    assert trading_pnl.quantity == 12
    assert trading_pnl.cost == -1236
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    buy_6_at_103 = Trade(6, 103)
    trading_pnl.add(buy_6_at_103)
    assert trading_pnl.quantity == 18
    assert trading_pnl.cost == -1854
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    sell_9_at_105 = Trade(-9, 105)
    trading_pnl.add(sell_9_at_105)
    assert trading_pnl.quantity == 9
    assert trading_pnl.cost == -936
    assert trading_pnl.realized == 27
    assert trading_pnl.avg_cost == 104


def test_long_to_short_with_splits_lifo():
    """long to short, splits, fifo"""

    trading_pnl = LifoTradingPnl()

    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 0

    buy_6_at_100 = Trade(6, 100)
    trading_pnl.add(buy_6_at_100)
    assert trading_pnl.quantity == 6
    assert trading_pnl.cost == -600
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 100

    buy_6_at_106 = Trade(6, 106)
    trading_pnl.add(buy_6_at_106)
    assert trading_pnl.quantity == 12
    assert trading_pnl.cost == -1236
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    buy_6_at_103 = Trade(6, 103)
    trading_pnl.add(buy_6_at_103)
    assert trading_pnl.quantity == 18
    assert trading_pnl.cost == -1854
    assert trading_pnl.realized == 0
    assert trading_pnl.avg_cost == 103

    sell_9_at_105 = Trade(-9, 105)
    trading_pnl.add(sell_9_at_105)
    assert trading_pnl.quantity == 9
    assert trading_pnl.cost == -918
    assert trading_pnl.realized == 9
    assert trading_pnl.avg_cost == 102


def test_long_to_short_fifo_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(1, 100))
    trading_pnl.add(Trade(-1, 102))
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 100)),
            ScaledTrade(Trade(-1, 102))
        )
    ]


def test_short_to_long_fifo_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(-1, 102))
    trading_pnl.add(Trade(1, 100))
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(-1, 102)),
            ScaledTrade(Trade(1, 100))
        )
    ]


def test_long_to_short_fifo_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(1, 102))
    trading_pnl.add(Trade(-1, 100))
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == -2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 102)),
            ScaledTrade(Trade(-1, 100))
        )
    ]


def test_short_to_long_fifo_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(-1, 100))
    trading_pnl.add(Trade(1, 102))
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == -2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(-1, 100)),
            ScaledTrade(Trade(1, 102))
        )
    ]


def test_long_sell_fifo_through_flat():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(1, 101))
    trading_pnl.add(Trade(-2, 102))
    assert trading_pnl.quantity == -1
    assert trading_pnl.cost == 102
    assert trading_pnl.realized == 1
    assert list(trading_pnl.unmatched) == [
        ScaledTrade(Trade(-2, 102), -1)
    ]
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 101), 1),
            ScaledTrade(Trade(-2, 102), -1)
        )
    ]


def test_short_buy_fifo_through_flat():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(-1, 102))
    trading_pnl.add(Trade(2, 101))
    assert trading_pnl.quantity == 1
    assert trading_pnl.cost == -101
    assert trading_pnl.realized == 1
    assert list(trading_pnl.unmatched) == [
        ScaledTrade(Trade(2, 101), 1)
    ]
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(-1, 102), -1),
            ScaledTrade(Trade(2, 101), 1)
        )
    ]


def test_one_buy_many_sells_fifo():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(10, 101))
    trading_pnl.add(Trade(-5, 102))
    assert trading_pnl.quantity == 5
    assert trading_pnl.cost == -505
    assert trading_pnl.realized == 5
    trading_pnl.add(Trade(-5, 104))
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 20
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(10, 101), 5),
            ScaledTrade(Trade(-5, 102), -5)
        ),
        MatchedTrade(
            ScaledTrade(Trade(10, 101), 5),
            ScaledTrade(Trade(-5, 104), -5)
        ),
    ]


def test_pnl():

    trading_pnl = FifoTradingPnl()

    # Buy 10 @ 100
    trading_pnl.add(Trade(10, 100))
    assert trading_pnl.pnl(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?
    assert trading_pnl.pnl(102) == (10, 100.0, 102, 0, 20)

    # What if we buy another 5 at 102?
    trading_pnl.add(Trade(10, 102))
    assert trading_pnl.pnl(102) == (20, 101.0, 102, 0, 20)

    # What is the P&L if the price goes to 104?
    assert trading_pnl.pnl(104) == (20, 101.0, 104, 0, 60)

    # What if we sell 10 at 104?
    trading_pnl.add(Trade(-10, 104))
    assert trading_pnl.pnl(104) == (10, 102.0, 104, 40, 20)

    # What if the price drops to 102?
    assert trading_pnl.pnl(102) == (10, 102.0, 102, 40, 0)

    # What if we sell 10 at 102?
    trading_pnl.add(Trade(-10, 102))
    assert trading_pnl.pnl(102) == (0, 0, 102, 40, 0)


def test_many_buys_one_sell_fifo():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(Trade(1, 100))
    trading_pnl.add(Trade(1, 102))
    trading_pnl.add(Trade(1, 101))
    trading_pnl.add(Trade(1, 104))
    trading_pnl.add(Trade(1, 103))
    trading_pnl.add(Trade(-5, 104))
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 100), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 102), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 101), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 104), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 103), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_buys_one_sell_lifo():

    trading_pnl = LifoTradingPnl()

    trading_pnl.add(Trade(1, 100))
    trading_pnl.add(Trade(1, 102))
    trading_pnl.add(Trade(1, 101))
    trading_pnl.add(Trade(1, 104))
    trading_pnl.add(Trade(1, 103))
    trading_pnl.add(Trade(-5, 104))
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 103), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 104), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 101), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 102), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 100), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_buys_one_sell_best_price():

    trading_pnl = BestPriceTradingPnl()

    trading_pnl.add(Trade(1, 100))
    trading_pnl.add(Trade(1, 102))
    trading_pnl.add(Trade(1, 101))
    trading_pnl.add(Trade(1, 104))
    trading_pnl.add(Trade(1, 103))
    trading_pnl.add(Trade(-5, 104))
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 100), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 101), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 102), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 103), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 104), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_sells_one_buy_best_price():

    trading_pnl = BestPriceTradingPnl()

    trading_pnl.add(Trade(-1, 100))
    trading_pnl.add(Trade(-1, 102))
    trading_pnl.add(Trade(-1, 101))
    trading_pnl.add(Trade(-1, 104))
    trading_pnl.add(Trade(-1, 103))
    trading_pnl.add(Trade(5, 104))
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(-1, 104), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 103), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 102), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 101), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 100), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
    ]


def test_many_buys_one_sell_worst_price():

    trading_pnl = WorstPriceTradingPnl()

    trading_pnl.add(Trade(1, 100))
    trading_pnl.add(Trade(1, 102))
    trading_pnl.add(Trade(1, 101))
    trading_pnl.add(Trade(1, 104))
    trading_pnl.add(Trade(1, 103))
    trading_pnl.add(Trade(-5, 104))
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(1, 104), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 103), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 102), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 101), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(1, 100), 1),
            ScaledTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_sells_one_buy_worst_price():

    trading_pnl = WorstPriceTradingPnl()

    trading_pnl.add(Trade(-1, 100))
    trading_pnl.add(Trade(-1, 102))
    trading_pnl.add(Trade(-1, 101))
    trading_pnl.add(Trade(-1, 104))
    trading_pnl.add(Trade(-1, 103))
    trading_pnl.add(Trade(5, 104))
    assert trading_pnl.matched == [
        MatchedTrade(
            ScaledTrade(Trade(-1, 100), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 101), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 102), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 103), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
        MatchedTrade(
            ScaledTrade(Trade(-1, 104), -1),
            ScaledTrade(Trade(5, 104), 1)
        ),
    ]
