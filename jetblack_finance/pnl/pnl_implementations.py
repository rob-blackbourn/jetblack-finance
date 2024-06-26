"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Generic, Sequence, TypeVar, cast

from .algorithm import IPartialTrade, ITrade, IPnlState
from .pnl_strip import PnlStrip
from .algorithm import add_trade

T = TypeVar('T', bound='ABCPnl')


class PartialTrade(IPartialTrade):

    def __init__(
            self,
            trade: ITrade,
            quantity: Decimal
    ) -> None:
        self._trade = trade
        self._quantity = quantity

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

    def __init__(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[IPartialTrade],
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> None:
        self._quantity = quantity
        self._cost = cost
        self._realized = realized
        self._unmatched = unmatched
        self._matched = matched

    def __add__(self, trade: Any) -> T:
        assert isinstance(trade, ITrade)
        state = add_trade(
            self,
            trade,
            self.create_pnl,
            self.create_partial_trade,
            self.push_unmatched,
            self.pop_unmatched,
            self.push_matched
        )
        return cast(T, state)

    @abstractmethod
    def create_pnl(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Sequence[IPartialTrade],
        matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> IPnlState:
        ...

    @abstractmethod
    def create_partial_trade(
        self,
        trade: ITrade,
        quantity: Decimal
    ) -> IPartialTrade:
        ...

    @abstractmethod
    def pop_unmatched(
            self,
            unmatched: Sequence[IPartialTrade]
    ) -> tuple[IPartialTrade, Sequence[IPartialTrade]]:
        ...

    @abstractmethod
    def push_unmatched(
        self,
        split_trade: IPartialTrade,
        unmatched: Sequence[IPartialTrade]
    ) -> Sequence[IPartialTrade]:
        ...

    @abstractmethod
    def push_matched(
            self,
            opening: IPartialTrade,
            closing: IPartialTrade,
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        ...

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
    def unmatched(self) -> Sequence[IPartialTrade]:
        return self._unmatched

    @property
    def matched(self) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        return self._matched

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)
        return -self.cost / self.quantity

    def unrealized(self, price: Decimal) -> Decimal:
        return self.quantity * price + self.cost

    def strip(self, price: Decimal) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            price,
            self.realized,
            self.unrealized(price)
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


class FifoPnl(ABCPnl['FifoPnl']):

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[IPartialTrade],
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> FifoPnl:
        return FifoPnl(quantity, cost, realized, unmatched, matched)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def pop_unmatched(
            self,
            unmatched: Sequence[IPartialTrade]
    ) -> tuple[IPartialTrade, Sequence[IPartialTrade]]:
        return unmatched[0], unmatched[1:]

    def push_unmatched(
            self,
            split_trade: IPartialTrade,
            unmatched: Sequence[IPartialTrade]
    ) -> Sequence[IPartialTrade]:
        return [split_trade] + list(unmatched)

    def push_matched(
            self,
            opening: IPartialTrade,
            closing: IPartialTrade,
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        matched_trade = (opening, closing)
        return list(matched) + [matched_trade]


class LifoPnl(ABCPnl):

    def create_pnl(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Sequence[IPartialTrade],
        matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> LifoPnl:
        return LifoPnl(quantity, cost, realized, unmatched, matched)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def pop_unmatched(
            self,
            unmatched: Sequence[IPartialTrade]
    ) -> tuple[IPartialTrade, Sequence[IPartialTrade]]:
        return unmatched[-1], unmatched[:-1]

    def push_unmatched(
            self,
            split_trade: IPartialTrade,
            unmatched: Sequence[IPartialTrade]
    ) -> Sequence[IPartialTrade]:
        return list(unmatched) + [split_trade]

    def push_matched(
            self,
            opening: IPartialTrade,
            closing: IPartialTrade,
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        return list(matched) + [(opening, closing)]


class BestPricePnl(ABCPnl):

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[IPartialTrade],
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> BestPricePnl:
        return BestPricePnl(quantity, cost, realized, unmatched, matched)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def pop_unmatched(
            self,
            unmatched: Sequence[IPartialTrade]
    ) -> tuple[IPartialTrade, Sequence[IPartialTrade]]:
        orders = sorted(unmatched, key=lambda x: x.price)
        order, orders = (
            (orders[0], orders[1:])
            if self.quantity > 0
            else (orders[-1], orders[:-1])
        )
        return order, orders

    def push_unmatched(
            self,
            split_trade: IPartialTrade,
            unmatched: Sequence[IPartialTrade]
    ) -> Sequence[IPartialTrade]:
        return list(unmatched) + [split_trade]

    def push_matched(
            self,
            opening: IPartialTrade,
            closing: IPartialTrade,
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        return list(matched) + [(opening, closing)]


class WorstPricePnl(ABCPnl):

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[IPartialTrade],
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> WorstPricePnl:
        return WorstPricePnl(quantity, cost, realized, unmatched, matched)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def pop_unmatched(
            self,
            unmatched: Sequence[IPartialTrade]
    ) -> tuple[IPartialTrade, Sequence[IPartialTrade]]:
        orders = sorted(unmatched, key=lambda x: x.price)
        order, orders = (
            (orders[-1], orders[:-1])
            if self.quantity > 0
            else (orders[0], orders[1:])
        )
        return order, orders

    def push_unmatched(
            self,
            split_trade: IPartialTrade,
            unmatched: Sequence[IPartialTrade]
    ) -> Sequence[IPartialTrade]:
        return list(unmatched) + [split_trade]

    def push_matched(
            self,
            opening: IPartialTrade,
            closing: IPartialTrade,
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        return list(matched) + [(opening, closing)]
