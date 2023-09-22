"""Trading P&L"""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Dict, Iterator, List, Mapping, Union

from jetblack_finance.pnl.order_pnl import IOrderPnl

from .order_pnl import IOrderPnl
from .symbol_pnl import SymbolPnl
from .isecurity import ISecurity
from .itrade import ITrade
from .trade_pnl_strip import TradePnlStrip


class TradingPnl:

    def __init__(
            self,
            order_pnl_factory: Callable[[], IOrderPnl],
            base_ccy: str
    ) -> None:
        self._book = SymbolPnl(order_pnl_factory)
        self.base_ccy = base_ccy

    def add(self, trade: ITrade) -> None:
        self._book[trade.security.symbol].add(trade.order)

    def pnl_strip(
            self,
            security: ISecurity,
            price: Union[int, Decimal],
            fx_rate: Decimal
    ) -> TradePnlStrip:
        if security.symbol not in self._book:
            raise KeyError()

        strip = self._book[security.symbol].pnl_strip(price)
        return TradePnlStrip(
            security.symbol,
            strip.quantity,
            strip.avg_cost,
            price,
            strip.realized,
            strip.unrealized,
            security.ccy,
            strip.realized * fx_rate,
            strip.unrealized * fx_rate,
            self.base_ccy
        )
