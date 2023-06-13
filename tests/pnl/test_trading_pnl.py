"""Tests for trading P&L"""

from jetblack_finance.pnl import TradingPnl, MatchedTrade, Trade


def test_long_to_short_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    trading_pnl = TradingPnl()

    trading_pnl.add(1, 100)
    trading_pnl.add(-1, 102)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(-1, 100, 102)]


def test_short_to_long_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    trading_pnl = TradingPnl()

    trading_pnl.add(-1, 102)
    trading_pnl.add(1, 100)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(1, 102, 100)]


def test_long_to_short_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    trading_pnl = TradingPnl()

    trading_pnl.add(1, 102)
    trading_pnl.add(-1, 100)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == -2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(-1, 102, 100)]


def test_short_to_long_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    trading_pnl = TradingPnl()

    trading_pnl.add(-1, 100)
    trading_pnl.add(1, 102)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == -2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(1, 100, 102)]


def test_long_sell_through_flat():

    trading_pnl = TradingPnl()

    trading_pnl.add(1, 101)
    trading_pnl.add(-2, 102)
    assert trading_pnl.quantity == -1
    assert trading_pnl.cost == 102
    assert trading_pnl.realized == 1
    assert list(trading_pnl.unmatched) == [Trade(-1, 102)]
    assert trading_pnl.matched == [MatchedTrade(-1, 101, 102)]


def test_short_buy_through_flat():

    trading_pnl = TradingPnl()

    trading_pnl.add(-1, 102)
    trading_pnl.add(2, 101)
    assert trading_pnl.quantity == 1
    assert trading_pnl.cost == -101
    assert trading_pnl.realized == 1
    assert list(trading_pnl.unmatched) == [Trade(1, 101)]
    assert trading_pnl.matched == [MatchedTrade(1, 102, 101)]


def test_one_buy_many_sells():

    trading_pnl = TradingPnl()

    trading_pnl.add(10, 101)
    trading_pnl.add(-5, 102)
    assert trading_pnl.quantity == 5
    assert trading_pnl.cost == -505
    assert trading_pnl.realized == 5
    trading_pnl.add(-5, 104)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 20
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [
        MatchedTrade(-5, 101, 102),
        MatchedTrade(-5, 101, 104),
    ]


def test_pnl():

    trading_pnl = TradingPnl()

    # Buy 10 @ 100
    trading_pnl.add(10, 100)
    assert trading_pnl.pnl(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?

    # What if we buy another 5 at 102?

    # What is the P&L if the price goes to 104?

    # What if we sell 5 at 104?

    # What if the price drops to 102?

    # What if we sell 10 at 102?
