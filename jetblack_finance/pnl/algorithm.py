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
from .trade import ITrade

CreatePnlState = Callable[[PnlState], PnlState]
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
CreatePartialTrade = Callable[[ITrade, Decimal], IPartialTrade]

def _extend_position(
        pnl: PnlState,
        partial_trade: IPartialTrade,
        create_pnl_state: CreatePnlState
) -> PnlState:
    return create_pnl_state(
        PnlState(
            pnl.quantity + partial_trade.quantity,
            pnl.cost - partial_trade.quantity * partial_trade.price,
            pnl.realized,
            list(pnl.unmatched) + [partial_trade],
            list(pnl.matched)
        )
    )


def _find_match(
        partial_trade: IPartialTrade,
        unmatched: Sequence[IPartialTrade],
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched
) -> tuple[Sequence[IPartialTrade], IPartialTrade, IPartialTrade, IPartialTrade | None]:
    # Fetch the next trade to match.
    matched_trade, unmatched = pop_unmatched(unmatched)

    if abs(partial_trade.quantity) > abs(matched_trade.quantity):

        # The trade is larger than the matched trade.
        # Split the trade by the matched trade quantity. This leaves a
        # remainder still to match.
        
        remainder = create_partial_trade(partial_trade.trade, partial_trade.quantity  + matched_trade.quantity)
        partial_trade = create_partial_trade(partial_trade.trade, -matched_trade.quantity)

    elif abs(partial_trade.quantity) < abs(matched_trade.quantity):

        # The matched trade is bigger than the current trade. Split the match
        # and return the spare to the unmatched.
        
        spare = create_partial_trade(matched_trade.trade, matched_trade.quantity + partial_trade.quantity)
        matched_trade = create_partial_trade(matched_trade.trade, -partial_trade.quantity)
        unmatched = push_unmatched(spare, unmatched)
        
        # As the entire trade has been filled there is no remainder.
        remainder = None

    else:
        
        # The trade quantity matches the matched trade quantity exactly.
        remainder = None

    return unmatched, partial_trade, matched_trade, remainder


def _match(
        pnl: PnlState,
        partial_trade: IPartialTrade,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> tuple[IPartialTrade | None, PnlState]:
    unmatched, partial_trade, matched_trade, remainder = _find_match(
        partial_trade,
        pnl.unmatched,
        create_partial_trade,
        push_unmatched,
        pop_unmatched
    )

    # Note that the open will have the opposite sign to the close.
    close_value = partial_trade.quantity * partial_trade.price
    open_cost = -(matched_trade.quantity * matched_trade.price)

    # The difference between the two costs is the realized value.
    realized = pnl.realized - (close_value - open_cost)
    # Remove the cost.
    cost = pnl.cost - open_cost
    # Remove the quantity.
    quantity = pnl.quantity - matched_trade.quantity

    matched = push_matched(matched_trade, partial_trade, pnl.matched)

    pnl = create_pnl_state(PnlState(quantity, cost, realized, unmatched, matched))

    return remainder, pnl


def _reduce_position(
        pnl: PnlState,
        partial_trade: IPartialTrade | None,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> PnlState:
    while partial_trade is not None and partial_trade.quantity != 0 and pnl.unmatched:
        partial_trade, pnl = _match(
            pnl,
            partial_trade,
            create_pnl_state,
            create_partial_trade,
            push_unmatched,
            pop_unmatched,
            push_matched,
        )

    if partial_trade is not None and partial_trade.quantity != 0:
        pnl = add_partial_trade(
            pnl,
            partial_trade,
            create_pnl_state,
            create_partial_trade,
            push_unmatched,
            pop_unmatched,
            push_matched,
        )

    return pnl


def add_partial_trade(
        pnl: PnlState,
        partial_trade: IPartialTrade,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> PnlState:
    if (
        # We are flat
        pnl.quantity == 0 or
        # We are long and buying
        (pnl.quantity > 0 and partial_trade.quantity > 0) or
        # We are short and selling.
        (pnl.quantity < 0 and partial_trade.quantity < 0)
    ):
        return _extend_position(pnl, partial_trade, create_pnl_state)
    else:
        return _reduce_position(
            pnl,
            partial_trade,
            create_pnl_state,
            create_partial_trade,
            push_unmatched,
            pop_unmatched,
            push_matched
        )

def add_trade(
        pnl: PnlState,
        trade: ITrade,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> PnlState:
    partial_trade = create_partial_trade(trade, trade.quantity)
    return add_partial_trade(
        pnl,
        partial_trade,
        create_pnl_state,
        create_partial_trade,
        push_unmatched,
        pop_unmatched,
        push_matched
    )