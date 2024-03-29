"""Symbol P&L"""

from __future__ import annotations

from typing import Callable, Dict, Iterator, MutableMapping

from .order_pnl import OrderPnl


class SymbolPnl(MutableMapping[str, OrderPnl]):

    def __init__(self, order_pnl_factory: Callable[[], OrderPnl]) -> None:
        self._order_pnl_factory = order_pnl_factory
        self._books: Dict[str, OrderPnl] = {}

    def __getitem__(self, symbol: str) -> OrderPnl:
        if symbol in self._books:
            return self._books[symbol]
        else:
            order_pnl = self._order_pnl_factory()
            self._books[symbol] = order_pnl
            return order_pnl

    def __setitem__(self, symbol: str, value: OrderPnl) -> None:
        self._books[symbol] = value

    def __len__(self) -> int:
        return len(self._books)

    def __iter__(self) -> Iterator[str]:
        return iter(self._books)

    def __contains__(self, symbol: object) -> bool:
        return symbol in self._books
