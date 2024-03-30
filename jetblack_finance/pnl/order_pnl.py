"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Callable, NamedTuple, Optional, Sequence, Tuple, Union

from .iorder import IOrder
from .matched_order import MatchedOrder
from .scaled_order import ScaledOrder
from .order_pnl_strip import OrderPnlStrip

Unmatched = Sequence[ScaledOrder]
Matched = Sequence[MatchedOrder]


class OrderPnlState(NamedTuple):

    quantity: Decimal
    cost: Decimal
    realized: Decimal
    unmatched: Unmatched
    matched: Matched

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


Create = Callable[
    [Decimal, Decimal, Decimal, Unmatched, Matched],
    OrderPnlState
]


def _extend_position(
        pnl: OrderPnlState,
        order: ScaledOrder,
) -> OrderPnlState:
    return OrderPnlState(
        pnl.quantity + order.quantity,
        pnl.cost - order.quantity * order.price,
        pnl.realized,
        list(pnl.unmatched) + [order],
        list(pnl.matched)
    )


def _find_match(
        order_candidate: ScaledOrder,
        unmatched: Sequence[ScaledOrder],
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]]
) -> Tuple[Unmatched, ScaledOrder, ScaledOrder, Optional[ScaledOrder]]:
    match_candidate, unmatched = pop_unmatched(unmatched)

    if abs(order_candidate.quantity) >= abs(match_candidate.quantity):
        # Split the candidate order to match the quantity. This leaves a
        # remaining order to match.
        close_order, order = order_candidate.split(
            -match_candidate.quantity
        )
        # The matching order is the whole of the candidate.
        open_order = match_candidate
    else:
        # The order is the entire candidate order. There is no remaining
        # order.
        close_order, order = order_candidate, None
        # Split the candidate match by the smaller order quantity, and
        # return the remaining unmatched.
        open_order, remaining_unmatched = match_candidate.split(
            -order_candidate.quantity
        )
        unmatched = push_unmatched(remaining_unmatched, unmatched)

    return unmatched, close_order, open_order, order


def _match(
        pnl: OrderPnlState,
        order: ScaledOrder,
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]],
) -> Tuple[Optional[ScaledOrder], OrderPnlState]:
    unmatched, close_order, open_order, remainder = _find_match(
        order,
        pnl.unmatched,
        push_unmatched,
        pop_unmatched
    )

    # Note that the open will have the opposite sign to the close.
    close_value = close_order.quantity * close_order.price
    open_cost = -(open_order.quantity * open_order.price)

    # The difference between the two costs is the realised value.
    realized = pnl.realized - (close_value - open_cost)
    # Remove the cost.
    cost = pnl.cost - open_cost
    # Remove the quantity.
    quantity = pnl.quantity - open_order.quantity

    matched = list(pnl.matched) + [MatchedOrder(open_order, close_order)]

    pnl = OrderPnlState(quantity, cost, realized, unmatched, matched)

    return remainder, pnl


def _reduce_position(
        pnl: OrderPnlState,
        order: Optional[ScaledOrder],
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]],
) -> OrderPnlState:
    while order is not None and order.quantity != 0 and pnl.unmatched:
        order, pnl = _match(
            pnl,
            order,
            push_unmatched,
            pop_unmatched,
        )

    if order is not None and order.quantity != 0:
        pnl = add_scaled_order(
            pnl,
            order,
            push_unmatched,
            pop_unmatched,
        )

    return pnl


def add_scaled_order(
        pnl: OrderPnlState,
        order: ScaledOrder,
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]]
) -> OrderPnlState:
    if (
        # We are flat
        pnl.quantity == 0 or
        # We are long and buying
        (pnl.quantity > 0 and order.quantity > 0) or
        # We are short and selling.
        (pnl.quantity < 0 and order.quantity < 0)
    ):
        return _extend_position(pnl, order)
    else:
        return _reduce_position(pnl, order, push_unmatched, pop_unmatched)


class OrderPnl:

    def __init__(
        self,
        quantity=Decimal(0),
        cost=Decimal(0),
        realized=Decimal(0),
        unmatched: Optional[Unmatched] = None,
        matched: Optional[Matched] = None
    ) -> None:
        self._state = OrderPnlState(
            quantity,
            cost,
            realized,
            unmatched or [],
            matched or []
        )

    def __add__(self, other: Any) -> OrderPnl:
        assert isinstance(other, IOrder)
        state = add_scaled_order(
            self._state,
            ScaledOrder(other),
            self._push_unmatched,
            self._pop_unmatched,
        )
        return self._create(state)

    def __sub__(self, other: Any) -> OrderPnl:
        assert isinstance(other, IOrder)
        state = add_scaled_order(
            self._state,
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
    def quantity(self) -> Decimal:
        return self._state.quantity

    @property
    def cost(self) -> Decimal:
        return self._state.cost

    @property
    def realized(self) -> Decimal:
        return self._state.realized

    @property
    def unmatched(self) -> Unmatched:
        return self._state.unmatched

    @property
    def matched(self) -> Matched:
        return self._state.matched

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
