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
from jetblack_finance.pnl.types import UnmatchedTrade

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
        return f"Trade(quantity={self.quantity},price={self.price})"


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
            UnmatchedTrade(Trade(1, 100), 0),
            UnmatchedTrade(Trade(-1, 102), 0)
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
            UnmatchedTrade(Trade(-1, 102), 0),
            UnmatchedTrade(Trade(1, 100), 0)
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
            UnmatchedTrade(Trade(1, 102), 0),
            UnmatchedTrade(Trade(-1, 100), 0)
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
            UnmatchedTrade(Trade(-1, 100), 0),
            UnmatchedTrade(Trade(1, 102), 0)
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
        UnmatchedTrade(Trade(-1, 102), 0)
    ]
    assert trading_pnl.matched == [
        MatchedTrade(
            UnmatchedTrade(Trade(1, 101), 0),
            UnmatchedTrade(Trade(-1, 102), 1)
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
        UnmatchedTrade(Trade(1, 101), 0)
    ]
    assert trading_pnl.matched == [
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 102), 0),
            UnmatchedTrade(Trade(1, 101), 1)
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
            UnmatchedTrade(Trade(5, 101), 0),
            UnmatchedTrade(Trade(-5, 102), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(5, 101), 1),
            UnmatchedTrade(Trade(-5, 104), 0)
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
            UnmatchedTrade(Trade(1, 100), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 102), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 101), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 104), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 103), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
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
            UnmatchedTrade(Trade(1, 103), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 104), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 101), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 102), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 100), 0),
            UnmatchedTrade(Trade(-1, 104), 0)
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
            UnmatchedTrade(Trade(1, 100), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 101), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 102), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 103), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 104), 0), UnmatchedTrade(Trade(-1, 104), 0)
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
            UnmatchedTrade(Trade(-1, 104), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 103), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 102), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 101), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 100), 0), UnmatchedTrade(Trade(1, 104), 0)
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
            UnmatchedTrade(Trade(1, 104), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 103), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 102), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 101), 0), UnmatchedTrade(Trade(-1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(1, 100), 0), UnmatchedTrade(Trade(-1, 104), 0)
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
            UnmatchedTrade(Trade(-1, 100), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 101), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 102), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 103), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
        MatchedTrade(
            UnmatchedTrade(Trade(-1, 104), 0), UnmatchedTrade(Trade(1, 104), 0)
        ),
    ]
