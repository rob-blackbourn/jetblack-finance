"""Tests for order P&L"""

from decimal import Decimal

from jetblack_finance.pnl import IMarketTrade
from jetblack_finance.pnl.impl.simple import (
    FifoPnl,
    LifoPnl,
    BestPricePnl,
    WorstPricePnl,
    PnlTrade,
)


class MarketTrade(IMarketTrade):
    """A simple trade"""

    def __init__(self, quantity: Decimal | int, price: Decimal | int) -> None:
        self._quantity = Decimal(quantity)
        self._price = Decimal(price)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, MarketTrade) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"


def test_long_to_short_with_splits_best_price():
    """long to short, splits, best price"""

    pnl = BestPricePnl(
        0, 0, 0,
        BestPricePnl.UnmatchedPool(),
        BestPricePnl.MatchedPool()
    )

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + MarketTrade(6, 100)  # Buy 6 @ 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + MarketTrade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -945
    assert pnl.realized == 36
    assert pnl.avg_cost == 105

    pnl = pnl + MarketTrade(-9, 107)  # Sell 9 @ 107
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 54
    assert pnl.avg_cost == 0


def test_long_to_short_with_splits_worst_price():
    """long to short, splits, worst price"""

    pnl = WorstPricePnl(
        0, 0, 0,
        WorstPricePnl.UnmatchedPool(), WorstPricePnl.MatchedPool()
    )

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + MarketTrade(6, 100)  # Buy 6 at 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + MarketTrade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -909
    assert pnl.realized == 0
    assert pnl.avg_cost == 101


def test_long_to_short_with_splits_fifo():
    """long to short, splits, fifo"""

    pnl = FifoPnl(
        0, 0, 0,
        FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool()
    )

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + MarketTrade(6, 100)  # Buy 6 @ 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + MarketTrade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -936
    assert pnl.realized == 27
    assert pnl.avg_cost == 104


def test_long_to_short_with_splits_lifo():
    """long to short, splits, fifo"""

    pnl = LifoPnl(0, 0, 0, LifoPnl.UnmatchedPool(), LifoPnl.MatchedPool())

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + MarketTrade(6, 100)  # Buy 6 @ 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + MarketTrade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + MarketTrade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -918
    assert pnl.realized == 9
    assert pnl.avg_cost == 102


def test_long_to_short_fifo_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(1, 100)
    pnl = pnl + MarketTrade(-1, 102)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 2
    assert len(pnl.unmatched) == 0
    expected = FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 100), 1),
            PnlTrade(MarketTrade(-1, 102), -1)
        ),
    ))
    assert pnl.matched == expected


def test_short_to_long_fifo_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(-1, 102)
    pnl = pnl + MarketTrade(1, 100)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(-1, 102), -1),
            PnlTrade(MarketTrade(1, 100), 1)
        ),
    ))


def test_long_to_short_fifo_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(1, 102)
    pnl = pnl + MarketTrade(-1, 100)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == -2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 102), 1),
            PnlTrade(MarketTrade(-1, 100), -1)
        ),
    ))


def test_short_to_long_fifo_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(-1, 100)
    pnl = pnl + MarketTrade(1, 102)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == -2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(-1, 100), -1),
            PnlTrade(MarketTrade(1, 102), 1)
        ),
    ))


def test_long_sell_fifo_through_flat():

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(1, 101)
    pnl = pnl + MarketTrade(-2, 102)
    assert pnl.quantity == -1
    assert pnl.cost == 102
    assert pnl.realized == 1
    assert pnl.unmatched == FifoPnl.UnmatchedPool((
        PnlTrade(MarketTrade(-2, 102), -1),
    ))
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 101), 1),
            PnlTrade(MarketTrade(-2, 102), -1)
        ),
    ))


def test_short_buy_fifo_through_flat():

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(-1, 102)
    pnl = pnl + MarketTrade(2, 101)
    assert pnl.quantity == 1
    assert pnl.cost == -101
    assert pnl.realized == 1
    assert pnl.unmatched == FifoPnl.UnmatchedPool((
        PnlTrade(MarketTrade(2, 101), 1),
    ))
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(-1, 102), -1),
            PnlTrade(MarketTrade(2, 101), 1)
        ),
    ))


def test_one_buy_many_sells_fifo():

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(10, 101)
    pnl = pnl + MarketTrade(-5, 102)
    assert pnl.quantity == 5
    assert pnl.cost == -505
    assert pnl.realized == 5
    pnl = pnl + MarketTrade(-5, 104)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 20
    assert len(pnl.unmatched) == 0
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(10, 101), 5),
            PnlTrade(MarketTrade(-5, 102), -5)
        ),
        (
            PnlTrade(MarketTrade(10, 101), 5),
            PnlTrade(MarketTrade(-5, 104), -5)
        ),
    ))


def test_pnl():

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    # Buy 10 @ 100
    pnl = pnl + MarketTrade(10, 100)
    assert pnl.strip(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?
    assert pnl.strip(102) == (10, 100.0, 102, 0, 20)

    # What if we buy another 5 at 102?
    pnl = pnl + MarketTrade(10, 102)
    assert pnl.strip(102) == (20, 101.0, 102, 0, 20)

    # What is the P&L if the price goes to 104?
    assert pnl.strip(104) == (20, 101.0, 104, 0, 60)

    # What if we sell 10 at 104?
    pnl = pnl + MarketTrade(-10, 104)
    assert pnl.strip(104) == (10, 102.0, 104, 40, 20)

    # What if the price drops to 102?
    assert pnl.strip(102) == (10, 102.0, 102, 40, 0)

    # What if we sell 10 at 102?
    pnl = pnl + MarketTrade(-10, 102)
    assert pnl.strip(102) == (0, 0, 102, 40, 0)


def test_many_buys_one_sell_fifo():

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(1, 100)
    pnl = pnl + MarketTrade(1, 102)
    pnl = pnl + MarketTrade(1, 101)
    pnl = pnl + MarketTrade(1, 104)
    pnl = pnl + MarketTrade(1, 103)
    pnl = pnl + MarketTrade(-5, 104)
    assert pnl.matched == FifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 100), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 102), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 101), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 104), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 103), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
    ))


def test_many_buys_one_sell_lifo():

    pnl = LifoPnl(0, 0, 0, LifoPnl.UnmatchedPool(), LifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(1, 100)
    pnl = pnl + MarketTrade(1, 102)
    pnl = pnl + MarketTrade(1, 101)
    pnl = pnl + MarketTrade(1, 104)
    pnl = pnl + MarketTrade(1, 103)
    pnl = pnl + MarketTrade(-5, 104)
    assert pnl.matched == LifoPnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 103), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 104), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 101), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 102), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 100), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
    ))


def test_many_buys_one_sell_best_price():

    pnl = BestPricePnl(
        0, 0, 0,
        BestPricePnl.UnmatchedPool(), BestPricePnl.MatchedPool()
    )

    pnl = pnl + MarketTrade(1, 100)
    pnl = pnl + MarketTrade(1, 102)
    pnl = pnl + MarketTrade(1, 101)
    pnl = pnl + MarketTrade(1, 104)
    pnl = pnl + MarketTrade(1, 103)
    pnl = pnl + MarketTrade(-5, 104)
    assert pnl.matched == BestPricePnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 100), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 101), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 102), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 103), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 104), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
    ))


def test_many_sells_one_buy_best_price():

    pnl = BestPricePnl(
        0, 0, 0,
        BestPricePnl.UnmatchedPool(), BestPricePnl.MatchedPool()
    )

    pnl = pnl + MarketTrade(-1, 100)
    pnl = pnl + MarketTrade(-1, 102)
    pnl = pnl + MarketTrade(-1, 101)
    pnl = pnl + MarketTrade(-1, 104)
    pnl = pnl + MarketTrade(-1, 103)
    pnl = pnl + MarketTrade(5, 104)

    expected = BestPricePnl.MatchedPool((
        (
            PnlTrade(MarketTrade(-1, 104), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 103), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 102), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 101), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 100), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
    ))

    assert pnl.matched == expected


def test_many_buys_one_sell_worst_price():

    pnl = WorstPricePnl(
        0, 0, 0,
        WorstPricePnl.UnmatchedPool(), WorstPricePnl.MatchedPool()
    )

    pnl = pnl + MarketTrade(1, 100)
    pnl = pnl + MarketTrade(1, 102)
    pnl = pnl + MarketTrade(1, 101)
    pnl = pnl + MarketTrade(1, 104)
    pnl = pnl + MarketTrade(1, 103)
    pnl = pnl + MarketTrade(-5, 104)

    expected = WorstPricePnl.MatchedPool((
        (
            PnlTrade(MarketTrade(1, 104), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 103), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 102), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 101), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
        (
            PnlTrade(MarketTrade(1, 100), 1),
            PnlTrade(MarketTrade(-5, 104), -1)
        ),
    ))

    assert pnl.matched == expected


def test_many_sells_one_buy_worst_price():

    pnl = WorstPricePnl(
        0, 0, 0,
        WorstPricePnl.UnmatchedPool(), WorstPricePnl.MatchedPool()
    )

    pnl = pnl + MarketTrade(-1, 100)
    pnl = pnl + MarketTrade(-1, 102)
    pnl = pnl + MarketTrade(-1, 101)
    pnl = pnl + MarketTrade(-1, 104)
    pnl = pnl + MarketTrade(-1, 103)
    pnl = pnl + MarketTrade(5, 104)

    expected = WorstPricePnl.MatchedPool((
        (
            PnlTrade(MarketTrade(-1, 100), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 101), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 102), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 103), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
        (
            PnlTrade(MarketTrade(-1, 104), -1),
            PnlTrade(MarketTrade(5, 104), 1)
        ),
    ))
    assert pnl.matched == expected


def test_fraction_quantities():

    pnl = FifoPnl(0, 0, 0, FifoPnl.UnmatchedPool(), FifoPnl.MatchedPool())

    pnl = pnl + MarketTrade(Decimal("10.17"), Decimal("2.54"))
    pnl = pnl + MarketTrade(Decimal("-8.17"), Decimal("2.12"))
    assert pnl.quantity == 2
    pnl = pnl + MarketTrade(Decimal("-1.5"), Decimal("2.05"))
    assert pnl.quantity == Decimal("0.5")
