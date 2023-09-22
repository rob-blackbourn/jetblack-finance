"""Symbol P&L"""

from __future__ import annotations

from typing import Callable, Dict, Iterator, Mapping

from jetblack_finance.pnl.order_pnl import IOrderPnl

from .order_pnl import IOrderPnl


class SymbolPnl(Mapping[str, IOrderPnl]):

    def __init__(self, order_pnl_factory: Callable[[], IOrderPnl]) -> None:
        self._order_pnl_factory = order_pnl_factory
        self._books: Dict[str, IOrderPnl] = {}

    def __getitem__(self, symbol: str) -> IOrderPnl:
        if symbol in self._books:
            return self._books[symbol]
        else:
            order_pnl = self._order_pnl_factory()
            self._books[symbol] = order_pnl
            return order_pnl

    def __len__(self) -> int:
        return len(self._books)

    def __iter__(self) -> Iterator[str]:
        return iter(self._books)

    def __contains__(self, symbol: object) -> bool:
        return symbol in self._books
