"""The algorithm for calculating P&L

A position consists of a number of executed buy or sell trades. When the
position is flat (the quantity of buys equals the quantity of sells) there is
an unambiguous result for the p/l (the amount spent minus the amount received).
Up until this point the p/l depends on which buys are matched with which sells,
and which unmatched trades remain.

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
* unmatched - trades which have not yet been completely matched.

If the new trade extends the position (a buy from a long or flat position or a
sell from a flat or short position) the quantity increases by that of the trade
and also the cost.

If the trade reduces the position a matching trade must be found. Taking FIFO
as the method, the oldest trade is taken. There are three possibilities: The
matching trade might be exactly the same quantity (but of opposite sign), the
trade might have the larger quantity, or the match might have the larger quantity.
Where the quantities don't match exactly there must be a split. If the match
quantity is greater, the match is split and the spare is returned to the unmatched.
If the trade is larger it is split and the remainder becomes the next trade to
match.
"""

from decimal import Decimal
from typing import Callable, Sequence

from .partial_trade import IPartialTrade
from .pnl_state import PnlState

CreatePnl = Callable[[PnlState], PnlState]
PushUnmatched = Callable[
    [IPartialTrade, Sequence[IPartialTrade]],
    Sequence[IPartialTrade]
]
PopUnmatched = Callable[
    [Sequence[IPartialTrade]],
    tuple[IPartialTrade, Sequence[IPartialTrade]]
]
PushMatched = Callable[
    [IPartialTrade, IPartialTrade, Sequence[tuple[IPartialTrade, IPartialTrade]]],
    Sequence[tuple[IPartialTrade, IPartialTrade]]
]
SplitTrade = Callable[[IPartialTrade, Decimal], tuple[IPartialTrade, IPartialTrade]]

def _extend_position(
        pnl: PnlState,
        trade: IPartialTrade,
        create_pnl: CreatePnl
) -> PnlState:
    """Extend a long or flat position with a buy, or a short or flat position
    with a sell.

    Extending a position simply accrues quantity, cost, and unmatched trades.

    Args:
        pnl (PnlState): The current p/p state.
        trade (ScaledTrade): The trade

    Returns:
        PnlState: The new p/l state.
    """
    return create_pnl(
        PnlState(
            pnl.quantity + trade.quantity,
            pnl.cost - trade.quantity * trade.price,
            pnl.realized,
            list(pnl.unmatched) + [trade],
            list(pnl.matched)
        )
    )


def _find_match(
        trade: IPartialTrade,
        unmatched: Sequence[IPartialTrade],
        split_trade: SplitTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched
) -> tuple[Sequence[IPartialTrade], IPartialTrade, IPartialTrade, IPartialTrade | None]:
    """Find a match for the trade from the unmatched trades.

    Args:
        trade (IPartialTrade): The trade to match.
        unmatched (Sequence[IPartialTrade]): The unmatched trades.
        split_trade (SplitTrade): Split a partial trade by quantity.
        push_unmatched (Callable[[IPartialTrade, Unmatched], Unmatched]): A
            function to add an trade to the unmatched trades.
        pop_unmatched (Callable[[Unmatched], tuple[IPartialTrade, Unmatched]]): A
            function to take an trade from the unmatched trades.

    Returns:
        tuple[Unmatched, IPartialTrade, IPartialTrade, IPartialTrade | None]: A tuple
            of the unmatched trades, the (potentially split) trade, the
            (potentially split) matched trade, and the remainder if the trade
            was split.
    """
    # Fetch the next trade to match.
    matched_trade, unmatched = pop_unmatched(unmatched)

    if abs(trade.quantity) > abs(matched_trade.quantity):
        # The trade is larger than the matched trade.
        # Split the trade by the matched trade quantity. This leaves a
        # remainder still to match.
        trade, remainder = split_trade(trade, -matched_trade.quantity)
    elif abs(trade.quantity) < abs(matched_trade.quantity):
        # The matched trade is bigger than the current trade. Split the match
        # and return the spare to the unmatched.
        matched_trade, spare = split_trade(matched_trade, -trade.quantity)
        unmatched = push_unmatched(spare, unmatched)
        # As the entire trade has been filled there is no remainder.
        remainder = None
    else:
        # The trade quantity matches the matched trade quantity exactly.
        remainder = None

    return unmatched, trade, matched_trade, remainder


def _match(
        pnl: PnlState,
        trade: IPartialTrade,
        create_pnl: CreatePnl,
        split_trade: SplitTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> tuple[IPartialTrade | None, PnlState]:
    """Match the trade with one from the unmatched trades.

    Args:
        pnl (PnlState): The current p/l state.
        trade (IPartialTrade): The trade to be filled.
        split_trade (SplitTrade): Split a partial trade by quantity.
        push_unmatched (Callable[[IPartialTrade, Unmatched], Unmatched]): A
            function to add an trade to the unmatched trades.
        pop_unmatched (Callable[[Unmatched], tuple[IPartialTrade, Unmatched]]): A
            function to take an trade from the unmatched trades.

    Returns:
        tuple[IPartialTrade | None, PnlState]: A tuple of the unfilled part
            of the trade (or None if the trade was completely filled) and the
            new p/l state.
    """
    unmatched, trade, matched_trade, remainder = _find_match(
        trade,
        pnl.unmatched,
        split_trade,
        push_unmatched,
        pop_unmatched
    )

    # Note that the open will have the opposite sign to the close.
    close_value = trade.quantity * trade.price
    open_cost = -(matched_trade.quantity * matched_trade.price)

    # The difference between the two costs is the realized value.
    realized = pnl.realized - (close_value - open_cost)
    # Remove the cost.
    cost = pnl.cost - open_cost
    # Remove the quantity.
    quantity = pnl.quantity - matched_trade.quantity

    matched = push_matched(matched_trade, trade, pnl.matched)

    pnl = create_pnl(PnlState(quantity, cost, realized, unmatched, matched))

    return remainder, pnl


def _reduce_position(
        pnl: PnlState,
        trade: IPartialTrade | None,
        create_pnl: CreatePnl,
        split_trade: SplitTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> PnlState:
    """Reduce a long position with a sell, or a short position with a buy.

    Args:
        pnl (PnlState): The current p/l state.
        trade (IPartialTrade | None): The trade.
        push_unmatched (Callable[[IPartialTrade, Unmatched], Unmatched]): A
            function to add an unmatched trade on to a sequence of unmatched
            trades.
        pop_unmatched (Callable[[Unmatched], tuple[IPartialTrade, Unmatched]]): A
            function to take an unmatched trade from a sequence of unmatched
            trades.

    Returns:
        PnlState: The new p/l state.
    """
    while trade is not None and trade.quantity != 0 and pnl.unmatched:
        trade, pnl = _match(
            pnl,
            trade,
            create_pnl,
            split_trade,
            push_unmatched,
            pop_unmatched,
            push_matched,
        )

    if trade is not None and trade.quantity != 0:
        pnl = add_partial_trade(
            pnl,
            trade,
            create_pnl,
            split_trade,
            push_unmatched,
            pop_unmatched,
            push_matched,
        )

    return pnl


def add_partial_trade(
        pnl: PnlState,
        trade: IPartialTrade,
        create_pnl: CreatePnl,
        split_trade: SplitTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> PnlState:
    """Add a partial trade creating a new p/l state.

    The trade could extend the position (buy to make a long or flat position
    longer, or sell to make a short or flat position shorter), or reduce the
    position (by selling from a long position, or buying back from a short
    position)

    Args:
        pnl (PnlState): The current p/l state.
        trade (IPartialTrade): The scaled trade to add.
        push_unmatched (Callable[[IPartialTrade, Unmatched], Unmatched]): A
            function to add a scaled trade to the sequence of unmatched trades.
        pop_unmatched (Callable[[Unmatched], tuple[IPartialTrade, Unmatched]]): A
            function to take a scaled trade from the sequence of unmatched
            trades.

    Returns:
        PnlState: The new p/l state.
    """
    if (
        # We are flat
        pnl.quantity == 0 or
        # We are long and buying
        (pnl.quantity > 0 and trade.quantity > 0) or
        # We are short and selling.
        (pnl.quantity < 0 and trade.quantity < 0)
    ):
        return _extend_position(pnl, trade, create_pnl)
    else:
        return _reduce_position(
            pnl,
            trade,
            create_pnl,
            split_trade,
            push_unmatched,
            pop_unmatched,
            push_matched
        )
