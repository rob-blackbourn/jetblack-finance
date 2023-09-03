"""Tests for trading P&L"""

from jetblack_finance.pnl import (
    FifoTradingPnl,
    LifoTradingPnl,
    BestPriceTradingPnl,
    WorstPriceTradingPnl,
    MatchedTrade,
    Trade,
)


def test_long_to_short_fifo_with_profit():
    """Buy 1 @ 100, then sell 1 @ 102 making 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(1, 100)
    trading_pnl.add(-1, 102)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(-1, 100, 102)]


def test_short_to_long_fifo_with_profit():
    """Sell 1 @ 102, then buy back 1 @ 101 making 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(-1, 102)
    trading_pnl.add(1, 100)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == 2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(1, 102, 100)]


def test_long_to_short_fifo_with_loss():
    """Buy 1 @ 102, then sell 1 @ 100 loosing 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(1, 102)
    trading_pnl.add(-1, 100)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == -2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(-1, 102, 100)]


def test_short_to_long_fifo_with_loss():
    """Sell 1 @ 100, then buy back 1 @ 102 loosing 2"""

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(-1, 100)
    trading_pnl.add(1, 102)
    assert trading_pnl.quantity == 0
    assert trading_pnl.cost == 0
    assert trading_pnl.realized == -2
    assert len(trading_pnl.unmatched) == 0
    assert trading_pnl.matched == [MatchedTrade(1, 100, 102)]


def test_long_sell_fifo_through_flat():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(1, 101)
    trading_pnl.add(-2, 102)
    assert trading_pnl.quantity == -1
    assert trading_pnl.cost == 102
    assert trading_pnl.realized == 1
    assert list(trading_pnl.unmatched) == [Trade(-1, 102)]
    assert trading_pnl.matched == [MatchedTrade(-1, 101, 102)]


def test_short_buy_fifo_through_flat():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(-1, 102)
    trading_pnl.add(2, 101)
    assert trading_pnl.quantity == 1
    assert trading_pnl.cost == -101
    assert trading_pnl.realized == 1
    assert list(trading_pnl.unmatched) == [Trade(1, 101)]
    assert trading_pnl.matched == [MatchedTrade(1, 102, 101)]


def test_one_buy_many_sells_fifo():

    trading_pnl = FifoTradingPnl()

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

    trading_pnl = FifoTradingPnl()

    # Buy 10 @ 100
    trading_pnl.add(10, 100)
    assert trading_pnl.pnl(100) == (10, 100, 100, 0, 0)

    # What is the P&L if the price goes to 102?
    assert trading_pnl.pnl(102) == (10, 100.0, 102, 0, 20)

    # What if we buy another 5 at 102?
    trading_pnl.add(10, 102)
    assert trading_pnl.pnl(102) == (20, 101.0, 102, 0, 20)

    # What is the P&L if the price goes to 104?
    assert trading_pnl.pnl(104) == (20, 101.0, 104, 0, 60)

    # What if we sell 10 at 104?
    trading_pnl.add(-10, 104)
    assert trading_pnl.pnl(104) == (10, 102.0, 104, 40, 20)

    # What if the price drops to 102?
    assert trading_pnl.pnl(102) == (10, 102.0, 102, 40, 0)

    # What if we sell 10 at 102?
    trading_pnl.add(-10, 102)
    assert trading_pnl.pnl(102) == (0, 0, 102, 40, 0)


def test_many_buys_one_sell_fifo():

    trading_pnl = FifoTradingPnl()

    trading_pnl.add(1, 100)
    trading_pnl.add(1, 102)
    trading_pnl.add(1, 101)
    trading_pnl.add(1, 104)
    trading_pnl.add(1, 103)
    trading_pnl.add(-5, 104)
    assert trading_pnl.matched == [
        MatchedTrade(-1, 100, 104),
        MatchedTrade(-1, 102, 104),
        MatchedTrade(-1, 101, 104),
        MatchedTrade(-1, 104, 104),
        MatchedTrade(-1, 103, 104),
    ]


def test_many_buys_one_sell_lifo():

    trading_pnl = LifoTradingPnl()

    trading_pnl.add(1, 100)
    trading_pnl.add(1, 102)
    trading_pnl.add(1, 101)
    trading_pnl.add(1, 104)
    trading_pnl.add(1, 103)
    trading_pnl.add(-5, 104)
    assert trading_pnl.matched == [
        MatchedTrade(-1, 103, 104),
        MatchedTrade(-1, 104, 104),
        MatchedTrade(-1, 101, 104),
        MatchedTrade(-1, 102, 104),
        MatchedTrade(-1, 100, 104),
    ]


def test_many_buys_one_sell_best_price():

    trading_pnl = BestPriceTradingPnl()

    trading_pnl.add(1, 100)
    trading_pnl.add(1, 102)
    trading_pnl.add(1, 101)
    trading_pnl.add(1, 104)
    trading_pnl.add(1, 103)
    trading_pnl.add(-5, 104)
    assert trading_pnl.matched == [
        MatchedTrade(-1, 100, 104),
        MatchedTrade(-1, 101, 104),
        MatchedTrade(-1, 102, 104),
        MatchedTrade(-1, 103, 104),
        MatchedTrade(-1, 104, 104),
    ]


def test_many_sells_one_buy_best_price():

    trading_pnl = BestPriceTradingPnl()

    trading_pnl.add(-1, 100)
    trading_pnl.add(-1, 102)
    trading_pnl.add(-1, 101)
    trading_pnl.add(-1, 104)
    trading_pnl.add(-1, 103)
    trading_pnl.add(5, 104)
    assert trading_pnl.matched == [
        MatchedTrade(1, 104, 104),
        MatchedTrade(1, 103, 104),
        MatchedTrade(1, 102, 104),
        MatchedTrade(1, 101, 104),
        MatchedTrade(1, 100, 104),
    ]


def test_many_buys_one_sell_worst_price():

    trading_pnl = WorstPriceTradingPnl()

    trading_pnl.add(1, 100)
    trading_pnl.add(1, 102)
    trading_pnl.add(1, 101)
    trading_pnl.add(1, 104)
    trading_pnl.add(1, 103)
    trading_pnl.add(-5, 104)
    assert trading_pnl.matched == [
        MatchedTrade(-1, 104, 104),
        MatchedTrade(-1, 103, 104),
        MatchedTrade(-1, 102, 104),
        MatchedTrade(-1, 101, 104),
        MatchedTrade(-1, 100, 104),
    ]


def test_many_sells_one_buy_worst_price():

    trading_pnl = WorstPriceTradingPnl()

    trading_pnl.add(-1, 100)
    trading_pnl.add(-1, 102)
    trading_pnl.add(-1, 101)
    trading_pnl.add(-1, 104)
    trading_pnl.add(-1, 103)
    trading_pnl.add(5, 104)
    assert trading_pnl.matched == [
        MatchedTrade(1, 100, 104),
        MatchedTrade(1, 101, 104),
        MatchedTrade(1, 102, 104),
        MatchedTrade(1, 103, 104),
        MatchedTrade(1, 104, 104),
    ]
