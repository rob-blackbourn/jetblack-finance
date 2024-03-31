"""Trading P&L"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Callable, Union

from .order_pnl import OrderPnl
from .isecurity import ISecurity
from .itrade import ITrade
from .trade_pnl_strip import TradePnlStrip


class TradingPnl:

    def __init__(
            self,
            order_pnl_factory: Callable[[], OrderPnl],
            base_ccy: str
    ) -> None:
        self._book: dict[str, OrderPnl] = defaultdict(order_pnl_factory)
        self.base_ccy = base_ccy

    def add(self, trade: ITrade) -> None:
        order_pnl = self._book[trade.security.symbol]
        order_pnl += trade.order
        self._book[trade.security.symbol] = order_pnl

    def strip(
            self,
            security: ISecurity,
            price: Union[int, Decimal],
            fx_rate: Decimal
    ) -> TradePnlStrip:
        if security.symbol not in self._book:
            raise KeyError()

        strip = self._book[security.symbol].strip(price)
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
