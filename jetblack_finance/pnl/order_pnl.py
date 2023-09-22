"""A calculator for P&L on orders"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import deque
from decimal import Decimal
from typing import Deque, List, Optional, Protocol, Tuple, Union

from .iorder import IOrder
from .matched_order import MatchedOrder
from .scaled_order import ScaledOrder
from .order_pnl_strip import OrderPnlStrip


class IOrderPnl(Protocol):

    @abstractmethod
    def add(self, order: IOrder) -> None:
        ...

    @property
    @abstractmethod
    def avg_cost(self) -> Decimal:
        ...

    @abstractmethod
    def unrealized(self, price: Union[Decimal, int]) -> Decimal:
        ...

    @abstractmethod
    def pnl_strip(self, price: Union[Decimal, int]) -> OrderPnlStrip:
        ...


class OrderPnl(IOrderPnl, metaclass=ABCMeta):
    """A class to calculate basic P&L on orders"""

    def __init__(self) -> None:
        self.quantity: Decimal = Decimal(0)
        self.cost: Decimal = Decimal(0)
        self.realized: Decimal = Decimal(0)
        self.unmatched: Deque[ScaledOrder] = deque()
        self.matched: List[MatchedOrder] = []

    def add(self, order: IOrder) -> None:
        self._add(ScaledOrder(order))

    def _add(self, order: ScaledOrder) -> None:
        if (
            # We are flat
            self.quantity == 0 or
            # We are long and buying
            (self.quantity > 0 and order.quantity > 0) or
            # We are short and selling.
            (self.quantity < 0 and order.quantity < 0)
        ):
            self._extend_position(order)
        else:
            self._reduce_position(order)

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)

        return -self.cost / self.quantity

    def unrealized(self, price: Union[Decimal, int]) -> Decimal:
        return self.quantity * price + self.cost

    def pnl_strip(self, price: Union[Decimal, int]) -> OrderPnlStrip:
        return OrderPnlStrip(
            self.quantity,
            self.avg_cost,
            price,
            self.realized,
            self.unrealized(price)
        )

    def _extend_position(self, order: ScaledOrder) -> None:
        self.cost -= order.quantity * order.price
        self.quantity += order.quantity
        self.unmatched.append(order)

    def _find_match(
            self,
            order_candidate: ScaledOrder
    ) -> Tuple[ScaledOrder, ScaledOrder, Optional[ScaledOrder]]:
        match_candidate = self.pop_unmatched()

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
            self.push_unmatched(remaining_unmatched)

        return close_order, open_order, order

    def _match(self, order: ScaledOrder) -> Optional[ScaledOrder]:
        close_order, open_order, remainder = self._find_match(order)

        # Note that the open will have the opposite sign to the close.
        close_value = close_order.quantity * close_order.price
        open_cost = -(open_order.quantity * open_order.price)

        # The difference between the two costs is the realised value.
        self.realized -= close_value - open_cost
        # Remove the cost.
        self.cost -= open_cost
        # Remove the quantity.
        self.quantity -= open_order.quantity

        self.matched.append(MatchedOrder(open_order, close_order))

        return remainder

    def _reduce_position(self, order: Optional[ScaledOrder]) -> None:
        while order is not None and order.quantity != 0 and self.unmatched:
            order = self._match(order)

        if order is not None and order.quantity != 0:
            self._add(order)

    @abstractmethod
    def pop_unmatched(self) -> ScaledOrder:
        ...

    @abstractmethod
    def push_unmatched(self, order: ScaledOrder) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


class FifoOrderPnl(OrderPnl):

    def pop_unmatched(self) -> ScaledOrder:
        return self.unmatched.popleft()

    def push_unmatched(self, order: ScaledOrder) -> None:
        self.unmatched.appendleft(order)


class LifoOrderPnl(OrderPnl):

    def pop_unmatched(self) -> ScaledOrder:
        return self.unmatched.pop()

    def push_unmatched(self, order: ScaledOrder) -> None:
        self.unmatched.append(order)


class BestPriceOrderPnl(OrderPnl):

    def pop_unmatched(self) -> ScaledOrder:
        orders = sorted(self.unmatched, key=lambda x: x.price)
        order = orders[0] if self.quantity > 0 else orders[-1]
        self.unmatched.remove(order)
        return order

    def push_unmatched(self, order: ScaledOrder) -> None:
        self.unmatched.append(order)


class WorstPriceOrderPnl(OrderPnl):

    def pop_unmatched(self) -> ScaledOrder:
        orders = sorted(self.unmatched, key=lambda x: x.price)
        order = orders[-1] if self.quantity > 0 else orders[0]
        self.unmatched.remove(order)
        return order

    def push_unmatched(self, order: ScaledOrder) -> None:
        self.unmatched.append(order)
