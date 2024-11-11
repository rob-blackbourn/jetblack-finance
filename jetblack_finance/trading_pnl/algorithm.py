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

from .types import IMarketTrade, IPnlTrade, IUnmatchedPool, IMatchedPool, TradingPnl


def _extend_position(
        state: TradingPnl,
        trade: IPnlTrade,
        unmatched: IUnmatchedPool
) -> TradingPnl:
    """Extend a position.

    This happens for:

    * A buy or sell from a flat position.
    * A buy from a long position.
    * A sell from a short position.

    In this situation no P&L is generated. The position size is increased, as is
    the cost of creating the position.

    Args:
        state (IPnlState): The state of the system.
        trade (IPnlTrade): The new trade.
        create_state (CreatePnlState): A factory method to create the new state.

    Returns:
        IPnlState: The new P&L state.
    """
    quantity = state.quantity + trade.quantity
    cost = state.cost - trade.quantity * trade.trade.price
    unmatched.push(trade)

    return TradingPnl(
        quantity,
        cost,
        state.realized,
    )


def _find_opening_trade(
        state: TradingPnl,
        closing_trade: IPnlTrade,
        unmatched: IUnmatchedPool
) -> tuple[IPnlTrade, IPnlTrade, IPnlTrade | None]:
    # Select an opening trade.
    opening_trade = unmatched.pop(state.quantity, state.cost)

    if abs(closing_trade.quantity) > abs(opening_trade.quantity):

        # The closing trade is larger than the opening trade.
        # Split the closing trade into two: one of the same size as the opening
        # trade, and a second with the unmatched quantity.

        matched_opening_trade = opening_trade
        matched_closing_trade = IPnlTrade(
            -opening_trade.quantity,
            closing_trade.trade,
        )
        unmatched_closing_trade = IPnlTrade(
            closing_trade.quantity - -opening_trade.quantity,
            closing_trade.trade,
        )

    elif abs(closing_trade.quantity) < abs(opening_trade.quantity):

        # The closing trade is smaller than the opening trade.
        # Split the opening trade into two: one of the same size as the closing
        # trade, and the second with the unmatched quantity. Return the unmatched
        # opening trade to the pool.

        matched_opening_trade = IPnlTrade(
            -closing_trade.quantity,
            opening_trade.trade,
        )
        matched_closing_trade = closing_trade
        unmatched_opening_trade = IPnlTrade(
            opening_trade.quantity + closing_trade.quantity,
            opening_trade.trade,
        )
        unmatched.push(unmatched_opening_trade)

        # As the entire closing trade has been filled there is no unmatched.
        unmatched_closing_trade = None

    else:

        # The closing trade quantity matches the opening trade quantity exactly.
        matched_opening_trade = opening_trade
        matched_closing_trade = closing_trade
        unmatched_closing_trade = None

    return matched_closing_trade, matched_opening_trade, unmatched_closing_trade


def _match(
        state: TradingPnl,
        closing_trade: IPnlTrade,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
) -> tuple[IPnlTrade | None, TradingPnl]:
    closing_trade, opening_trade, unmatched_opening_trade = _find_opening_trade(
        state,
        closing_trade,
        unmatched
    )

    matched.push(opening_trade, closing_trade)

    # Note that the open will have the opposite sign to the close.
    close_value = closing_trade.quantity * closing_trade.trade.price
    open_cost = -(opening_trade.quantity * opening_trade.trade.price)

    state = TradingPnl(
        state.quantity - opening_trade.quantity,
        state.cost - open_cost,
        state.realized + (open_cost - close_value),
    )

    return unmatched_opening_trade, state


def _reduce_position(
        state: TradingPnl,
        reducing_trade: IPnlTrade | None,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
) -> TradingPnl:
    while reducing_trade is not None and reducing_trade.quantity != 0 and len(unmatched) > 0:
        reducing_trade, state = _match(
            state,
            reducing_trade,
            unmatched,
            matched
        )

    if reducing_trade is not None and reducing_trade.quantity != 0:
        state = add_pnl_trade(
            state,
            reducing_trade,
            unmatched,
            matched
        )

    return state


def add_pnl_trade(
        state: TradingPnl,
        trade: IPnlTrade,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
) -> TradingPnl:
    if (
        # We are flat
        state.quantity == 0 or
        # We are long and buying
        (state.quantity > 0 and trade.quantity > 0) or
        # We are short and selling.
        (state.quantity < 0 and trade.quantity < 0)
    ):
        return _extend_position(
            state,
            trade,
            unmatched
        )
    else:
        return _reduce_position(
            state,
            trade,
            unmatched,
            matched
        )


def add_trade(
        state: TradingPnl,
        market_trade: IMarketTrade,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
) -> TradingPnl:
    return add_pnl_trade(
        state,
        IPnlTrade(market_trade.quantity, market_trade),
        unmatched,
        matched
    )
