"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Sequence

from .trade import ITrade
from .partial_trade import PartialTrade, IPartialTrade
from .pnl_strip import PnlStrip
from .pnl_state import PnlState
from .algorithm import add_partial_trade


class ABCPnl:

    def __init__(
        self,
        pnl_state: PnlState | None = None,
    ) -> None:
        if pnl_state is None:
            pnl_state = PnlState(
                Decimal(0),
                Decimal(0),
                Decimal(0),
                (),
                (),
            )
        self._pnl_state = pnl_state

    def __add__(self, trade: Any) -> ABCPnl:
        assert isinstance(trade, ITrade)
        split_trade = self.create_partial_trade(trade, trade.quantity)
        state = add_partial_trade(
            self._pnl_state,
            split_trade,
            self.create_pnl,
            self.create_partial_trade,
            self.push_unmatched,
            self.pop_unmatched,
            self.push_matched
        )
        return self.create(state)

    @abstractmethod
    def create(
        self,
        pnl_state: PnlState
    ) -> ABCPnl:
        ...

    @abstractmethod
    def create_partial_trade(
        self,
        trade: ITrade,
        quantity: Decimal
    ) -> IPartialTrade:
        ...


    @abstractmethod
    def create_pnl(self, pnl_state: PnlState) -> PnlState:
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
        return self._pnl_state.quantity

    @property
    def cost(self) -> Decimal:
        return self._pnl_state.cost

    @property
    def realized(self) -> Decimal:
        return self._pnl_state.realized

    @property
    def unmatched(self) -> Sequence[IPartialTrade]:
        return self._pnl_state.unmatched

    @property
    def matched(self) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        return self._pnl_state.matched

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


class FifoPnl(ABCPnl):

    def create(
        self,
        pnl_state: PnlState
    ) -> FifoPnl:
        return FifoPnl(pnl_state)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def create_pnl(self, pnl_state: PnlState) -> PnlState:
        return pnl_state

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

    def create(
        self,
        pnl_state: PnlState
    ) -> LifoPnl:
        return LifoPnl(pnl_state)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def create_pnl(self, pnl_state: PnlState) -> PnlState:
        return pnl_state

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

    def create(
        self,
        pnl_state: PnlState
    ) -> BestPricePnl:
        return BestPricePnl(pnl_state)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def create_pnl(self, pnl_state: PnlState) -> PnlState:
        return pnl_state

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

    def create(
        self,
        pnl_state: PnlState
    ) -> WorstPricePnl:
        return WorstPricePnl(pnl_state)

    def create_partial_trade(self, trade: ITrade, quantity: Decimal) -> IPartialTrade:
        return PartialTrade(trade, quantity)

    def create_pnl(self, pnl_state: PnlState) -> PnlState:
        return pnl_state

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
