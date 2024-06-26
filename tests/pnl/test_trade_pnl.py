"""Tests for order P&L"""

from decimal import Decimal

from jetblack_finance.pnl import (
    FifoPnl,
    LifoPnl,
    BestPricePnl,
    WorstPricePnl,
    ITrade,
    PartialTrade,
)


class Trade(ITrade):
    """A simple trade"""

    def __init__(self, quantity: Decimal, price: Decimal) -> None:
        self._quantity = quantity
        self._price = price

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Trade) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"


def test_long_to_short_with_splits_best_price():
    """long to short, splits, best price"""

    pnl = BestPricePnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + Trade(6, 100)  # Buy 6 @ 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + Trade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -945
    assert pnl.realized == 36
    assert pnl.avg_cost == 105

    pnl = pnl + Trade(-9, 107)  # Sell 9 @ 107
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 54
    assert pnl.avg_cost == 0


def test_long_to_short_with_splits_worst_price():
    """long to short, splits, worst price"""

    pnl = WorstPricePnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + Trade(6, 100)  # Buy 6 at 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + Trade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -909
    assert pnl.realized == 0
    assert pnl.avg_cost == 101


def test_long_to_short_with_splits_fifo():
    """long to short, splits, fifo"""

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + Trade(6, 100)  # Buy 6 @ 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + Trade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -936
    assert pnl.realized == 27
    assert pnl.avg_cost == 104


def test_long_to_short_with_splits_lifo():
    """long to short, splits, fifo"""

    pnl = LifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 0
    assert pnl.avg_cost == 0

    pnl = pnl + Trade(6, 100)  # Buy 6 @ 100
    assert pnl.quantity == 6
    assert pnl.cost == -600
    assert pnl.realized == 0
    assert pnl.avg_cost == 100

    pnl = pnl + Trade(6, 106)  # Buy 6 @ 106
    assert pnl.quantity == 12
    assert pnl.cost == -1236
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(6, 103)  # Buy 6 @ 103
    assert pnl.quantity == 18
    assert pnl.cost == -1854
    assert pnl.realized == 0
    assert pnl.avg_cost == 103

    pnl = pnl + Trade(-9, 105)  # Sell 9 @ 105
    assert pnl.quantity == 9
    assert pnl.cost == -918
    assert pnl.realized == 9
    assert pnl.avg_cost == 102


def test_long_to_short_fifo_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 100)
    pnl = pnl + Trade(-1, 102)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 100), 1),
            PartialTrade(Trade(-1, 102), -1)
        )
    ]


def test_short_to_long_fifo_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(-1, 102)
    pnl = pnl + Trade(1, 100)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == [
        (
            PartialTrade(Trade(-1, 102), -1),
            PartialTrade(Trade(1, 100), 1)
        )
    ]


def test_long_to_short_fifo_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 102)
    pnl = pnl + Trade(-1, 100)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == -2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 102), 1),
            PartialTrade(Trade(-1, 100), -1)
        )
    ]


def test_short_to_long_fifo_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(-1, 100)
    pnl = pnl + Trade(1, 102)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == -2
    assert len(pnl.unmatched) == 0
    assert pnl.matched == [
        (
            PartialTrade(Trade(-1, 100), -1),
            PartialTrade(Trade(1, 102), 1)
        )
    ]


def test_long_sell_fifo_through_flat():

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 101)
    pnl = pnl + Trade(-2, 102)
    assert pnl.quantity == -1
    assert pnl.cost == 102
    assert pnl.realized == 1
    assert list(pnl.unmatched) == [
        PartialTrade(Trade(-2, 102), -1)
    ]
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 101), 1),
            PartialTrade(Trade(-2, 102), -1)
        )
    ]


def test_short_buy_fifo_through_flat():

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(-1, 102)
    pnl = pnl + Trade(2, 101)
    assert pnl.quantity == 1
    assert pnl.cost == -101
    assert pnl.realized == 1
    assert list(pnl.unmatched) == [
        PartialTrade(Trade(2, 101), 1)
    ]
    assert pnl.matched == [
        (
            PartialTrade(Trade(-1, 102), -1),
            PartialTrade(Trade(2, 101), 1)
        )
    ]


def test_one_buy_many_sells_fifo():

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(10, 101)
    pnl = pnl + Trade(-5, 102)
    assert pnl.quantity == 5
    assert pnl.cost == -505
    assert pnl.realized == 5
    pnl = pnl + Trade(-5, 104)
    assert pnl.quantity == 0
    assert pnl.cost == 0
    assert pnl.realized == 20
    assert len(pnl.unmatched) == 0
    assert pnl.matched == [
        (
            PartialTrade(Trade(10, 101), 5),
            PartialTrade(Trade(-5, 102), -5)
        ),
        (
            PartialTrade(Trade(10, 101), 5),
            PartialTrade(Trade(-5, 104), -5)
        ),
    ]


def test_pnl():

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    # Buy 10 @ 100
    pnl = pnl + Trade(10, 100)
    assert pnl.strip(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?
    assert pnl.strip(102) == (10, 100.0, 102, 0, 20)

    # What if we buy another 5 at 102?
    pnl = pnl + Trade(10, 102)
    assert pnl.strip(102) == (20, 101.0, 102, 0, 20)

    # What is the P&L if the price goes to 104?
    assert pnl.strip(104) == (20, 101.0, 104, 0, 60)

    # What if we sell 10 at 104?
    pnl = pnl + Trade(-10, 104)
    assert pnl.strip(104) == (10, 102.0, 104, 40, 20)

    # What if the price drops to 102?
    assert pnl.strip(102) == (10, 102.0, 102, 40, 0)

    # What if we sell 10 at 102?
    pnl = pnl + Trade(-10, 102)
    assert pnl.strip(102) == (0, 0, 102, 40, 0)


def test_many_buys_one_sell_fifo():

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 100)
    pnl = pnl + Trade(1, 102)
    pnl = pnl + Trade(1, 101)
    pnl = pnl + Trade(1, 104)
    pnl = pnl + Trade(1, 103)
    pnl = pnl + Trade(-5, 104)
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 100), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 102), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 101), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 104), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 103), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_buys_one_sell_lifo():

    pnl = LifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 100)
    pnl = pnl + Trade(1, 102)
    pnl = pnl + Trade(1, 101)
    pnl = pnl + Trade(1, 104)
    pnl = pnl + Trade(1, 103)
    pnl = pnl + Trade(-5, 104)
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 103), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 104), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 101), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 102), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 100), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_buys_one_sell_best_price():

    pnl = BestPricePnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 100)
    pnl = pnl + Trade(1, 102)
    pnl = pnl + Trade(1, 101)
    pnl = pnl + Trade(1, 104)
    pnl = pnl + Trade(1, 103)
    pnl = pnl + Trade(-5, 104)
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 100), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 101), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 102), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 103), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 104), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_sells_one_buy_best_price():

    pnl = BestPricePnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(-1, 100)
    pnl = pnl + Trade(-1, 102)
    pnl = pnl + Trade(-1, 101)
    pnl = pnl + Trade(-1, 104)
    pnl = pnl + Trade(-1, 103)
    pnl = pnl + Trade(5, 104)
    assert pnl.matched == [
        (
            PartialTrade(Trade(-1, 104), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 103), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 102), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 101), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 100), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
    ]


def test_many_buys_one_sell_worst_price():

    pnl = WorstPricePnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(1, 100)
    pnl = pnl + Trade(1, 102)
    pnl = pnl + Trade(1, 101)
    pnl = pnl + Trade(1, 104)
    pnl = pnl + Trade(1, 103)
    pnl = pnl + Trade(-5, 104)
    assert pnl.matched == [
        (
            PartialTrade(Trade(1, 104), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 103), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 102), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 101), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
        (
            PartialTrade(Trade(1, 100), 1),
            PartialTrade(Trade(-5, 104), -1)
        ),
    ]


def test_many_sells_one_buy_worst_price():

    pnl = WorstPricePnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(-1, 100)
    pnl = pnl + Trade(-1, 102)
    pnl = pnl + Trade(-1, 101)
    pnl = pnl + Trade(-1, 104)
    pnl = pnl + Trade(-1, 103)
    pnl = pnl + Trade(5, 104)
    assert pnl.matched == [
        (
            PartialTrade(Trade(-1, 100), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 101), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 102), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 103), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
        (
            PartialTrade(Trade(-1, 104), -1),
            PartialTrade(Trade(5, 104), 1)
        ),
    ]


def test_fraction_quantities():

    pnl = FifoPnl(Decimal(0), Decimal(0), Decimal(0), (), ())

    pnl = pnl + Trade(Decimal("10.17"), Decimal("2.54"))
    pnl = pnl + Trade(Decimal("-8.17"), Decimal("2.12"))
    assert pnl.quantity == 2
    pnl = pnl + Trade(Decimal("-1.5"), Decimal("2.05"))
    assert pnl.quantity == Decimal("0.5")
