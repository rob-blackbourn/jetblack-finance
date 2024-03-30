"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Any, Callable, Optional, Sequence, Tuple, Union

from .iorder import IOrder
from .matched_order import MatchedOrder
from .scaled_order import ScaledOrder
from .order_pnl_strip import OrderPnlStrip

Unmatched = Sequence[ScaledOrder]
Matched = Sequence[MatchedOrder]


class OrderPnl:

    def __init__(
        self,
        quantity=Decimal(0),
        cost=Decimal(0),
        realized=Decimal(0),
        unmatched: Optional[Unmatched] = None,
        matched: Optional[Matched] = None
    ) -> None:
        self._quantity = quantity
        self._cost = cost
        self._realized = realized
        self._unmatched = unmatched or []
        self._matched = matched or []

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
    def unmatched(self) -> Unmatched:
        return self._unmatched

    @property
    def matched(self) -> Matched:
        return self._matched

    def __add__(self, other: Any) -> OrderPnl:
        assert isinstance(other, IOrder)
        return add_scaled_order(
            self,
            ScaledOrder(other),
            self._push_unmatched,
            self._pop_unmatched,
            self._create
        )

    def __sub__(self, other: Any) -> OrderPnl:
        assert isinstance(other, IOrder)
        return add_scaled_order(
            self,
            -ScaledOrder(other),
            self._push_unmatched,
            self._pop_unmatched,
            self._create
        )

    @abstractmethod
    def _create(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Unmatched,
        matched: Matched
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

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


Create = Callable[
    [Decimal, Decimal, Decimal, Unmatched, Matched],
    OrderPnl
]


def _extend_position(pnl: OrderPnl, order: ScaledOrder, create: Create) -> OrderPnl:
    return create(
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
        pnl: OrderPnl,
        order: ScaledOrder,
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]],
        create: Create
) -> Tuple[Optional[ScaledOrder], OrderPnl]:
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

    pnl = create(quantity, cost, realized, unmatched, matched)

    return remainder, pnl


def _reduce_position(
        pnl: OrderPnl,
        order: Optional[ScaledOrder],
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]],
        create: Create
) -> OrderPnl:
    while order is not None and order.quantity != 0 and pnl.unmatched:
        order, pnl = _match(
            pnl,
            order,
            push_unmatched,
            pop_unmatched,
            create
        )

    if order is not None and order.quantity != 0:
        pnl = add_scaled_order(
            pnl,
            order,
            push_unmatched,
            pop_unmatched,
            create
        )

    return pnl


def add_scaled_order(
        pnl: OrderPnl,
        order: ScaledOrder,
        push_unmatched: Callable[[ScaledOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[ScaledOrder, Unmatched]],
        create: Create
) -> OrderPnl:
    if (
        # We are flat
        pnl.quantity == 0 or
        # We are long and buying
        (pnl.quantity > 0 and order.quantity > 0) or
        # We are short and selling.
        (pnl.quantity < 0 and order.quantity < 0)
    ):
        return _extend_position(pnl, order, create)
    else:
        return _reduce_position(pnl, order, push_unmatched, pop_unmatched, create)


class FifoOrderPnl(OrderPnl):

    def _create(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Unmatched,
        matched: Matched
    ) -> OrderPnl:
        return FifoOrderPnl(quantity, cost, realized, unmatched, matched)

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        return unmatched[0], unmatched[1:]

    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        return [order] + list(unmatched)


class LifoOrderPnl(OrderPnl):

    def _create(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Unmatched,
        matched: Matched
    ) -> OrderPnl:
        return LifoOrderPnl(quantity, cost, realized, unmatched, matched)

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ScaledOrder, Unmatched]:
        return unmatched[-1], unmatched[:-1]

    def _push_unmatched(self, order: ScaledOrder, unmatched: Unmatched) -> Unmatched:
        return list(unmatched) + [order]


class BestPriceOrderPnl(OrderPnl):

    def _create(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Unmatched,
        matched: Matched
    ) -> OrderPnl:
        return BestPriceOrderPnl(quantity, cost, realized, unmatched, matched)

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
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Unmatched,
        matched: Matched
    ) -> OrderPnl:
        return WorstPriceOrderPnl(quantity, cost, realized, unmatched, matched)

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
