"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Callable, Optional, Union

from .matched_trade import MatchedTrade
from .trade import ITrade
from .split_trade import SplitTrade, ISplitTrade
from .pnl_strip import PnlStrip
from .pnl_state import PnlState, Matched, Unmatched
from .algorithm import add_split_trade


class ABCPnl(PnlState):

    def __init__(
        self,
        quantity=Decimal(0),
        cost=Decimal(0),
        realized=Decimal(0),
        unmatched: Optional[Unmatched] = None,
        matched: Optional[Matched] = None,
        factory: Optional[Callable[[ITrade], ISplitTrade]] = None
    ) -> None:
        super().__init__(
            quantity,
            cost,
            realized,
            unmatched or [],
            matched or [],
        )
        self._factory = factory or SplitTrade

    def __add__(self, other: Any) -> ABCPnl:
        assert isinstance(other, ITrade)
        split_trade = self._factory(other)
        state = add_split_trade(
            self,
            split_trade,
            self._push_unmatched,
            self._pop_unmatched,
            self._push_matched
        )
        return self._create(state)

    @abstractmethod
    def _create(
        self,
        state: PnlState
    ) -> ABCPnl:
        ...

    @abstractmethod
    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ISplitTrade, Unmatched]:
        ...

    @abstractmethod
    def _push_unmatched(self, order: ISplitTrade, unmatched: Unmatched) -> Unmatched:
        ...

    @abstractmethod
    def _push_matched(self, opening: ISplitTrade, closing: ISplitTrade, matched: Matched) -> Matched:
        ...

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)
        return -self.cost / self.quantity

    def unrealized(self, price: Union[Decimal, int]) -> Decimal:
        return self.quantity * price + self.cost

    def strip(self, price: Union[Decimal, int]) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            price,
            self.realized,
            self.unrealized(price)
        )


class FifoPnl(ABCPnl):

    def _create(
        self,
        state: PnlState
    ) -> FifoPnl:
        return FifoPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ISplitTrade, Unmatched]:
        return unmatched[0], unmatched[1:]

    def _push_unmatched(self, order: ISplitTrade, unmatched: Unmatched) -> Unmatched:
        return [order] + list(unmatched)

    def _push_matched(self, opening: ISplitTrade, closing: ISplitTrade, matched: Matched) -> Matched:
        return list(matched) + [MatchedTrade(opening, closing)]


class LifoPnl(ABCPnl):

    def _create(
        self,
        state: PnlState
    ) -> LifoPnl:
        return LifoPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ISplitTrade, Unmatched]:
        return unmatched[-1], unmatched[:-1]

    def _push_unmatched(self, order: ISplitTrade, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]

    def _push_matched(self, opening: ISplitTrade, closing: ISplitTrade, matched: Matched) -> Matched:
        return list(matched) + [MatchedTrade(opening, closing)]


class BestPricePnl(ABCPnl):

    def _create(
        self,
        state: PnlState
    ) -> BestPricePnl:
        return BestPricePnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ISplitTrade, Unmatched]:
        orders = sorted(unmatched, key=lambda x: x.price)
        order, orders = (
            (orders[0], orders[1:])
            if self.quantity > 0
            else (orders[-1], orders[:-1])
        )
        return order, orders

    def _push_unmatched(self, order: ISplitTrade, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]

    def _push_matched(self, opening: ISplitTrade, closing: ISplitTrade, matched: Matched) -> Matched:
        return list(matched) + [MatchedTrade(opening, closing)]


class WorstPricePnl(ABCPnl):

    def _create(
        self,
        state: PnlState
    ) -> WorstPricePnl:
        return WorstPricePnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ISplitTrade, Unmatched]:
        orders = sorted(unmatched, key=lambda x: x.price)
        order, orders = (
            (orders[-1], orders[:-1])
            if self.quantity > 0
            else (orders[0], orders[1:])
        )
        return order, orders

    def _push_unmatched(self, order: ISplitTrade, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]

    def _push_matched(self, opening: ISplitTrade, closing: ISplitTrade, matched: Matched) -> Matched:
        return list(matched) + [MatchedTrade(opening, closing)]
