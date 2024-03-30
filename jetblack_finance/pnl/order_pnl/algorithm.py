"""A calculator for P&L on orders"""

from typing import Callable, Optional, Sequence, Tuple

from .matched_order import MatchedOrder
from .scaled_order import ScaledOrder
from .order_pnl_state import OrderPnlState, Unmatched


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
