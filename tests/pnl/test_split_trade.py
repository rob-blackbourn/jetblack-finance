"""Tests for scaled orders"""

from jetblack_finance.pnl import SplitTrade, Trade


def test_split_long():
    order = SplitTrade(Trade(10, 2))
    matched, order = order.split(4)
    assert matched.quantity == 4
    assert order.quantity == 6

    matched, order = order.split(4)
    assert matched.quantity == 4
    assert order.quantity == 2

    matched, order = order.split(2)
    assert matched.quantity == 2
    assert order.quantity == 0


def test_split_short():
    order = SplitTrade(Trade(-10, 2))
    matched, order = order.split(-4)
    assert matched.quantity == -4
    assert order.quantity == -6

    matched, order = order.split(-4)
    assert matched.quantity == -4
    assert order.quantity == -2

    matched, order = order.split(-2)
    assert matched.quantity == -2
    assert order.quantity == 0
