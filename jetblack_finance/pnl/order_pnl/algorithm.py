"""The algorithm for calculating P&L

A position consists of a number of executed buy or sell orders. When the
position is flat (the quantity of buys equals the quantity of sells) there is
an unambiguous result for the p/l (the amount spent minus the amount received).
Up until this point the p/l depends on which buys are matched with which sells,
and which unmatched orders remain.

Typically, accountants prefer a FIFO (first in, first out) style of matching.
So if there has be three buys, a sell matches against the earliest buy.

Traders sometimes prefer a "worst price" approach, were a sell is matched
against the highest price buy.

Regardless of the approach the p/l can be characterized by the following
properties:

* quantity - how much of the asset is held.
* cost - how much has it cost to accrue the asset.
* realized - how much profit (or loss) was realized by selling from a long
  position, or buying from a short.
* unmatched - orders which have not yet been completely matched.

If the new order extends the position (a buy from a long or flat position or a
sell from a flat or short position) the quantity increases by that of the order
and also the cost.

If the order reduces the position a matching order must be found. Taking FIFO
as the method, the oldest order is taken. There are three possibilities: The
matching order might be exactly the same quantity (but of opposite sign), the
order might have the larger quantity, or the match might have the larger quantity.
Where the quantities don't match exactly there must be a split. If the match
quantity is greater, the match is split and the spare is returned to the unmatched.
If the order is larger it is split and the remainder becomes the next order to
match.
"""

from typing import Callable, Optional, Sequence, Tuple

from .matched_order import MatchedOrder
from .split_order import SplitOrder
from .order_pnl_state import OrderPnlState, Unmatched


def _extend_position(
        pnl: OrderPnlState,
        order: SplitOrder,
) -> OrderPnlState:
    """Extend a long or flat position with a buy, or a short or flat position
    with a sell.

    Extending a position simply accrues quantity, cost, and unmatched orders.

    Args:
        pnl (OrderPnlState): The current p/p state.
        order (ScaledOrder): The order

    Returns:
        OrderPnlState: The new order state.
    """
    return OrderPnlState(
        pnl.quantity + order.quantity,
        pnl.cost - order.quantity * order.price,
        pnl.realized,
        list(pnl.unmatched) + [order],
        list(pnl.matched)
    )


def _find_match(
        order: SplitOrder,
        unmatched: Sequence[SplitOrder],
        push_unmatched: Callable[[SplitOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[SplitOrder, Unmatched]]
) -> Tuple[Unmatched, SplitOrder, SplitOrder, Optional[SplitOrder]]:
    """Find a match for the order from the unmatched orders.

    Args:
        order (SplitOrder): The order to match.
        unmatched (Sequence[SplitOrder]): The unmatched orders.
        push_unmatched (Callable[[SplitOrder, Unmatched], Unmatched]): A
            function to add an order to the unmatched orders.
        pop_unmatched (Callable[[Unmatched], tuple[SplitOrder, Unmatched]]): A
            function to take an order from the unmatched orders.

    Returns:
        Tuple[Unmatched, SplitOrder, SplitOrder, Optional[SplitOrder]]: A tuple
            of the unmatched orders, the (potentially split) order, the
            (potentially split) matched order, and the remainder if the order
            was split.
    """
    # Fetch the next order to match.
    matched_order, unmatched = pop_unmatched(unmatched)

    if abs(order.quantity) > abs(matched_order.quantity):
        # The order is larger than the matched order.
        # Split the order by matched order quantity. This leaves a
        # remainder still to match.
        order, remainder = order.split(-matched_order.quantity)
    elif abs(order.quantity) < abs(matched_order.quantity):
        # The matched order is bigger than the current order. Split the match
        # and return the spare to the unmatched.
        matched_order, spare = matched_order.split(-order.quantity)
        unmatched = push_unmatched(spare, unmatched)
        # As the entire order has been filled there is no remainder.
        remainder = None
    else:
        # The order quantity matches the matched order quantity exactly.
        remainder = None

    return unmatched, order, matched_order, remainder


def _match(
        pnl: OrderPnlState,
        order: SplitOrder,
        push_unmatched: Callable[[SplitOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[SplitOrder, Unmatched]],
) -> Tuple[Optional[SplitOrder], OrderPnlState]:
    """Match the order with one from the unmatched orders.

    Args:
        pnl (OrderPnlState): The current p/l state.
        order (SplitOrder): The order to be filled.
        push_unmatched (Callable[[SplitOrder, Unmatched], Unmatched]): A
            function to add an order to the unmatched orders.
        pop_unmatched (Callable[[Unmatched], tuple[SplitOrder, Unmatched]]): A
            function to take an order from the unmatched orders.

    Returns:
        Tuple[Optional[SplitOrder], OrderPnlState]: A tuple of the unfilled part
            of the order (or None if the order was completely filled) and the
            new p/l state.
    """
    unmatched, order, matched_order, remainder = _find_match(
        order,
        pnl.unmatched,
        push_unmatched,
        pop_unmatched
    )

    # Note that the open will have the opposite sign to the close.
    close_value = order.quantity * order.price
    open_cost = -(matched_order.quantity * matched_order.price)

    # The difference between the two costs is the realized value.
    realized = pnl.realized - (close_value - open_cost)
    # Remove the cost.
    cost = pnl.cost - open_cost
    # Remove the quantity.
    quantity = pnl.quantity - matched_order.quantity

    matched = list(pnl.matched) + [MatchedOrder(matched_order, order)]

    pnl = OrderPnlState(quantity, cost, realized, unmatched, matched)

    return remainder, pnl


def _reduce_position(
        pnl: OrderPnlState,
        order: Optional[SplitOrder],
        push_unmatched: Callable[[SplitOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[SplitOrder, Unmatched]],
) -> OrderPnlState:
    """Reduce a long position with a sell, or a short position with a buy.

    Args:
        pnl (OrderPnlState): The current p/l state.
        order (Optional[ScaledOrder]): The order
        push_unmatched (Callable[[ScaledOrder, Unmatched], Unmatched]): A
            function to add an unmatched order on to a sequence of unmatched
            orders.
        pop_unmatched (Callable[[Unmatched], tuple[ScaledOrder, Unmatched]]): A
            function to take an unmatched order from a sequence of unmatched
            orders.

    Returns:
        OrderPnlState: The new p/l state.
    """
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
        order: SplitOrder,
        push_unmatched: Callable[[SplitOrder, Unmatched], Unmatched],
        pop_unmatched: Callable[[Unmatched], tuple[SplitOrder, Unmatched]]
) -> OrderPnlState:
    """Add an order creating a new p/l state.

    The order could extend the position (buy to make a long or flat position
    longer, or sell to make a short or flat position shorter), or reduce the
    position (by selling from a long position, or buying back from a short
    position)

    Args:
        pnl (OrderPnlState): The current p/l state.
        order (ScaledOrder): The order to add.
        push_unmatched (Callable[[ScaledOrder, Unmatched], Unmatched]): A
            function to add a scaled order to the sequence of unmatched orders.
        pop_unmatched (Callable[[Unmatched], tuple[ScaledOrder, Unmatched]]): A
            function to take a scaled order from the sequence of unmatched
            orders.

    Returns:
        OrderPnlState: The new p/l state.
    """
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
