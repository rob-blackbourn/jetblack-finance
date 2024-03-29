"""Tests for trading pnl"""

from jetblack_finance.pnl import FifoOrderPnl
from jetblack_finance.pnl.trading_pnl import TradingPnl

from .utils import Order, Trade, Security


def test_smoke():
    trading_pnl = TradingPnl(FifoOrderPnl, 'USD')

    ibm = Security('IBM', 'USD')

    # Buy 10 @ 100
    trading_pnl.add(Trade(ibm, Order(10, 100)))
    # (quantity, avg_cost, price, realized, unrealized)
    assert trading_pnl.pnl_strip(ibm, 100, 1) == (
        'IBM', 10, 100, 100, 0, 0, 'USD', 0, 0, 'USD')

    # What is the P&L if the price goes to 102?
    assert trading_pnl.pnl_strip(ibm, 102, 1) == (
        'IBM', 10, 100.0, 102, 0, 20, 'USD', 0, 20, 'USD')

    # What if we buy another 5 at 102?
    trading_pnl.add(Trade(ibm, Order(10, 102)))
    assert trading_pnl.pnl_strip(ibm, 102, 1) == (
        'IBM', 20, 101.0, 102, 0, 20, 'USD', 0, 20, 'USD')

    # What is the P&L if the price goes to 104?
    assert trading_pnl.pnl_strip(ibm, 104, 1) == (
        'IBM', 20, 101.0, 104, 0, 60, 'USD', 0, 60, 'USD')

    # What if we sell 10 at 104?
    trading_pnl.add(Trade(ibm, Order(-10, 104)))
    assert trading_pnl.pnl_strip(ibm, 104, 1) == (
        'IBM', 10, 102.0, 104, 40, 20, 'USD', 40, 20, 'USD')

    # What if the price drops to 102?
    assert trading_pnl.pnl_strip(ibm, 102, 1) == (
        'IBM', 10, 102.0, 102, 40, 0, 'USD', 40, 0, 'USD')

    # What if we sell 10 at 102?
    trading_pnl.add(Trade(ibm, Order(-10, 102)))
    assert trading_pnl.pnl_strip(ibm, 102, 1) == (
        'IBM', 0, 0, 102, 40, 0, 'USD', 40, 0, 'USD')
