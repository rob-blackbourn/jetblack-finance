"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Optional, Union

from .iorder import IOrder
from .scaled_order import ScaledOrder
from .order_pnl_strip import OrderPnlStrip
from .order_pnl_state import OrderPnlState, Matched, Unmatched
from .algorithm import add_scaled_order


class OrderPnl(OrderPnlState):

    def __init__(
        self,
        quantity=Decimal(0),
        cost=Decimal(0),
        realized=Decimal(0),
        unmatched: Optional[Unmatched] = None,
        matched: Optional[Matched] = None
    ) -> None:
        super().__init__(
            quantity,
            cost,
            realized,
            unmatched or [],
            matched or [],
        )

    def __add__(self, other: Any) -> OrderPnl:
        assert isinstance(other, IOrder)
        state = add_scaled_order(
            self,
            ScaledOrder(other),
            self._push_unmatched,
            self._pop_unmatched,
        )
        return self._create(state)

    def __sub__(self, other: Any) -> OrderPnl:
        assert isinstance(other, IOrder)
        state = add_scaled_order(
            self,
            -ScaledOrder(other),
            self._push_unmatched,
            self._pop_unmatched,
        )
        return self._create(state)

    @abstractmethod
    def _create(
        self,
        state: OrderPnlState
    ) -> OrderPnl:
        ...

    @abstractmethod
    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        ...

    @abstractmethod
    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        ...

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)
        return -self.cost / self.quantity

    def unrealized(self, price: Union[Decimal, int]) -> Decimal:
        return self.quantity * price + self.cost

    def strip(self, price: Union[Decimal, int]) -> OrderPnlStrip:
        return OrderPnlStrip(
            self.quantity,
            self.avg_cost,
            price,
            self.realized,
            self.unrealized(price)
        )


class FifoOrderPnl(OrderPnl):

    def _create(
        self,
        state: OrderPnlState
    ) -> FifoOrderPnl:
        return FifoOrderPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        return unmatched[0], unmatched[1:]

    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        return [order] + list(unmatched)


class LifoOrderPnl(OrderPnl):

    def _create(
        self,
        state: OrderPnlState
    ) -> LifoOrderPnl:
        return LifoOrderPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        return unmatched[-1], unmatched[:-1]

    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]


class BestPriceOrderPnl(OrderPnl):

    def _create(
        self,
        state: OrderPnlState
    ) -> BestPriceOrderPnl:
        return BestPriceOrderPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        orders = sorted(unmatched, key=lambda x: x.price)
        order, orders = (
            (orders[0], orders[1:])
            if self.quantity > 0
            else (orders[-1], orders[:-1])
        )
        return order, orders

    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]


class WorstPriceOrderPnl(OrderPnl):

    def _create(
        self,
        state: OrderPnlState
    ) -> WorstPriceOrderPnl:
        return WorstPriceOrderPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        orders = sorted(unmatched, key=lambda x: x.price)
        order, orders = (
            (orders[-1], orders[:-1])
            if self.quantity > 0
            else (orders[0], orders[1:])
        )
        return order, orders

    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]
