"""A calculator for P&L on orders"""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from ..types import (
    IPnlTrade,
    IMarketTrade,
    IMatchedPool,
    IUnmatchedPool
)


class MatchedPool(IMatchedPool):

    def __init__(self, pool: Sequence[tuple[IPnlTrade, IPnlTrade]] = ()) -> None:
        self._pool = pool

    def push(self, opening: IPnlTrade, closing: IPnlTrade) -> None:
        matched_trade = (opening, closing)
        self._pool = tuple((*self._pool, matched_trade))

    def __len__(self) -> int:
        return len(self._pool)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, MatchedPool) and
            value._pool == self._pool
        )

    def __str__(self) -> str:
        return str(self._pool)


class UnmatchedPool:
    class Fifo(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPnlTrade] = ()) -> None:
            self._pool = pool

        def push(self, pnl_trade: IPnlTrade) -> None:
            self._pool = tuple((*self._pool, pnl_trade))

        def pop(self, _quantity: Decimal, _cost: Decimal) -> IPnlTrade:
            trade, self._pool = (self._pool[0], self._pool[1:])
            return trade

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, UnmatchedPool.Fifo) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    class Lifo(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPnlTrade] = ()) -> None:
            self._pool = pool

        def push(self, pnl_trade: IPnlTrade) -> None:
            self._pool = tuple((*self._pool, pnl_trade))

        def pop(self, _quantity: Decimal, _cost: Decimal) -> IPnlTrade:
            trade, self._pool = (self._pool[-1], self._pool[:-1])
            return trade

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, UnmatchedPool.Lifo) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    class BestPrice(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPnlTrade] = ()) -> None:
            self._pool = pool

        def push(self, pnl_trade: IPnlTrade) -> None:
            self._pool = tuple((*self._pool, pnl_trade))

        def pop(self, quantity: Decimal, _cost: Decimal) -> IPnlTrade:
            self._pool = sorted(self._pool, key=lambda x: x.trade.price)
            trade, self._pool = (
                (self._pool[0], self._pool[1:])
                if quantity >= 0
                else (self._pool[-1], self._pool[:-1])
            )
            return trade

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, UnmatchedPool.BestPrice) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    class WorstPrice(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPnlTrade] = ()) -> None:
            self._pool = pool

        def push(self, pnl_trade: IPnlTrade) -> None:
            self._pool = tuple((*self._pool, pnl_trade))

        def pop(self, quantity: Decimal, _cost: Decimal) -> IPnlTrade:
            self._pool = sorted(self._pool, key=lambda x: x.trade.price)
            trade, self._pool = (
                (self._pool[-1], self._pool[:-1])
                if quantity > 0
                else (self._pool[0], self._pool[1:])
            )
            return trade

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, UnmatchedPool.WorstPrice) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)


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
