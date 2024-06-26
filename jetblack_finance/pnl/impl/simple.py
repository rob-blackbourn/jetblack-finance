"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Generic, Sequence, TypeVar, cast

from ..algorithm import (
    IPartialTrade,
    ITrade,
    IPnlState,
    IMatchedPool,
    IUnmatchedPool
)
from ..pnl_strip import PnlStrip
from ..algorithm import add_trade

T = TypeVar('T', bound='ABCPnl')


class PartialTrade(IPartialTrade):

    def __init__(
            self,
            trade: ITrade,
            quantity: Decimal | int
    ) -> None:
        self._trade = trade
        self._quantity = Decimal(quantity)

    @property
    def trade(self) -> ITrade:
        return self._trade

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._trade.price

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, PartialTrade) and
            self._trade == value._trade and
            self.quantity == value.quantity
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.price}"


class ABCPnl(IPnlState, Generic[T]):

    class MatchedPool(IMatchedPool):

        def __init__(self, pool: Sequence[tuple[IPartialTrade, IPartialTrade]] = ()) -> None:
            self._pool = pool

        def push(self, opening: IPartialTrade, closing: IPartialTrade) -> None:
            matched_trade = (opening, closing)
            self._pool = tuple((*self._pool, matched_trade))

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, FifoPnl.MatchedPool) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    def __init__(
            self,
            quantity: Decimal | int,
            cost: Decimal | int,
            realized: Decimal | int,
            unmatched: IUnmatchedPool,
            matched: IMatchedPool
    ) -> None:
        self._quantity = Decimal(quantity)
        self._cost = Decimal(cost)
        self._realized = Decimal(realized)
        self._unmatched = unmatched
        self._matched = matched

    def __add__(self, trade: Any) -> T:
        assert isinstance(trade, ITrade)
        state = add_trade(
            self,
            trade,
            self.create_pnl,
            self.create_partial_trade,
        )
        return cast(T, state)

    @abstractmethod
    def create_pnl(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
    ) -> IPnlState:
        ...

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def cost(self) -> Decimal:
        return self._cost

    @property
    def realized(self) -> Decimal:
        return self._realized

    @property
    def unmatched(self) -> IUnmatchedPool:
        return self._unmatched

    @property
    def matched(self) -> IMatchedPool:
        return self._matched

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)
        return -self.cost / self.quantity

    def unrealized(self, price: Decimal) -> Decimal:
        return self.quantity * price + self.cost

    def strip(self, price: Decimal | int) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            Decimal(price),
            self.realized,
            self.unrealized(Decimal(price))
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


class FifoPnl(ABCPnl['FifoPnl']):

    class UnmatchedPool(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPartialTrade] = ()) -> None:
            self._pool = pool

        def push(self, partial_trade: IPartialTrade) -> None:
            self._pool = tuple((*self._pool, partial_trade))

        def pop(self, pnl_state: IPnlState) -> IPartialTrade:
            partial_trade, self._pool = (self._pool[0], self._pool[1:])
            return partial_trade

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, FifoPnl.UnmatchedPool) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: IUnmatchedPool,
            matched: IMatchedPool
    ) -> FifoPnl:
        return FifoPnl(
            quantity,
            cost,
            realized,
            unmatched,
            matched
        )


class LifoPnl(ABCPnl):

    class UnmatchedPool(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPartialTrade] = ()) -> None:
            self._pool = pool

        def push(self, partial_trade: IPartialTrade) -> None:
            self._pool = tuple((*self._pool, partial_trade))

        def pop(self, pnl_state: IPnlState) -> IPartialTrade:
            partial_trade, self._pool = (self._pool[-1], self._pool[:-1])
            return partial_trade

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, LifoPnl.UnmatchedPool) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    def create_pnl(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
    ) -> LifoPnl:
        return LifoPnl(
            quantity,
            cost,
            realized,
            unmatched,
            matched
        )


class BestPricePnl(ABCPnl):

    class UnmatchedPool(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPartialTrade] = ()) -> None:
            self._pool = pool

        def push(self, partial_trade: IPartialTrade) -> None:
            self._pool = tuple((*self._pool, partial_trade))

        def pop(self, pnl_state: IPnlState) -> IPartialTrade:
            self._pool = sorted(self._pool, key=lambda x: x.price)
            order, self._pool = (
                (self._pool[0], self._pool[1:])
                if pnl_state.quantity > 0
                else (self._pool[-1], self._pool[:-1])
            )
            return order

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, BestPricePnl.UnmatchedPool) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: IUnmatchedPool,
            matched: IMatchedPool
    ) -> BestPricePnl:
        return BestPricePnl(
            quantity,
            cost,
            realized,
            unmatched,
            matched
        )


class WorstPricePnl(ABCPnl):

    class UnmatchedPool(IUnmatchedPool):

        def __init__(self, pool: Sequence[IPartialTrade] = ()) -> None:
            self._pool = pool

        def push(self, partial_trade: IPartialTrade) -> None:
            self._pool = tuple((*self._pool, partial_trade))

        def pop(self, pnl_state: IPnlState) -> IPartialTrade:
            self._pool = sorted(self._pool, key=lambda x: x.price)
            order, self._pool = (
                (self._pool[-1], self._pool[:-1])
                if pnl_state.quantity > 0
                else (self._pool[0], self._pool[1:])
            )
            return order

        def __len__(self) -> int:
            return len(self._pool)

        def __eq__(self, value: object) -> bool:
            return (
                isinstance(value, WorstPricePnl.UnmatchedPool) and
                value._pool == self._pool
            )

        def __str__(self) -> str:
            return str(self._pool)

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: IUnmatchedPool,
            matched: IMatchedPool
    ) -> WorstPricePnl:
        return WorstPricePnl(
            quantity,
            cost,
            realized,
            unmatched,
            matched
        )
