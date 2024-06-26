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

from abc import abstractmethod
from decimal import Decimal
from typing import Callable, Protocol, Sequence, runtime_checkable


@runtime_checkable
class ITrade(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...


class IPartialTrade(Protocol):

    @property
    @abstractmethod
    def trade(self) -> ITrade:
        ...

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...


class IPnlState(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def cost(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def realized(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def unmatched(self) -> Sequence[IPartialTrade]:
        ...

    @property
    @abstractmethod
    def matched(self) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        ...


CreatePnlState = Callable[
    [
        Decimal,
        Decimal,
        Decimal,
        Sequence[IPartialTrade],
        Sequence[tuple[IPartialTrade, IPartialTrade]]
    ],
    IPnlState
]
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
        pnl_state: IPnlState,
        partial_trade: IPartialTrade,
        create_pnl_state: CreatePnlState,
        push_unmatched: PushUnmatched
) -> IPnlState:
    quantity = pnl_state.quantity + partial_trade.quantity
    cost = pnl_state.cost - partial_trade.quantity * partial_trade.price
    realized = pnl_state.realized
    unmatched = push_unmatched(partial_trade, pnl_state.unmatched)
    matched = pnl_state.matched

    return create_pnl_state(
        quantity,
        cost,
        realized,
        unmatched,
        matched
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

        remainder = create_partial_trade(
            partial_trade.trade, partial_trade.quantity + matched_trade.quantity)
        partial_trade = create_partial_trade(
            partial_trade.trade, -matched_trade.quantity)

    elif abs(partial_trade.quantity) < abs(matched_trade.quantity):

        # The matched trade is bigger than the current trade. Split the match
        # and return the spare to the unmatched.

        spare = create_partial_trade(
            matched_trade.trade, matched_trade.quantity + partial_trade.quantity)
        matched_trade = create_partial_trade(
            matched_trade.trade, -partial_trade.quantity)
        unmatched = push_unmatched(spare, unmatched)

        # As the entire trade has been filled there is no remainder.
        remainder = None

    else:

        # The trade quantity matches the matched trade quantity exactly.
        remainder = None

    return unmatched, partial_trade, matched_trade, remainder


def _match(
        pnl_state: IPnlState,
        partial_trade: IPartialTrade,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> tuple[IPartialTrade | None, IPnlState]:
    unmatched, partial_trade, matched_trade, remainder = _find_match(
        partial_trade,
        pnl_state.unmatched,
        create_partial_trade,
        push_unmatched,
        pop_unmatched
    )

    # Note that the open will have the opposite sign to the close.
    close_value = partial_trade.quantity * partial_trade.price
    open_cost = -(matched_trade.quantity * matched_trade.price)

    # The difference between the two costs is the realized value.
    realized = pnl_state.realized - (close_value - open_cost)
    # Remove the cost.
    cost = pnl_state.cost - open_cost
    # Remove the quantity.
    quantity = pnl_state.quantity - matched_trade.quantity

    matched = push_matched(matched_trade, partial_trade, pnl_state.matched)

    pnl_state = create_pnl_state(quantity, cost, realized, unmatched, matched)

    return remainder, pnl_state


def _reduce_position(
        pnl_state: IPnlState,
        partial_trade: IPartialTrade | None,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> IPnlState:
    while partial_trade is not None and partial_trade.quantity != 0 and pnl_state.unmatched:
        partial_trade, pnl_state = _match(
            pnl_state,
            partial_trade,
            create_pnl_state,
            create_partial_trade,
            push_unmatched,
            pop_unmatched,
            push_matched,
        )

    if partial_trade is not None and partial_trade.quantity != 0:
        pnl_state = add_partial_trade(
            pnl_state,
            partial_trade,
            create_pnl_state,
            create_partial_trade,
            push_unmatched,
            pop_unmatched,
            push_matched,
        )

    return pnl_state


def add_partial_trade(
        pnl_state: IPnlState,
        partial_trade: IPartialTrade,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> IPnlState:
    if (
        # We are flat
        pnl_state.quantity == 0 or
        # We are long and buying
        (pnl_state.quantity > 0 and partial_trade.quantity > 0) or
        # We are short and selling.
        (pnl_state.quantity < 0 and partial_trade.quantity < 0)
    ):
        return _extend_position(
            pnl_state,
            partial_trade,
            create_pnl_state,
            push_unmatched
        )
    else:
        return _reduce_position(
            pnl_state,
            partial_trade,
            create_pnl_state,
            create_partial_trade,
            push_unmatched,
            pop_unmatched,
            push_matched
        )


def add_trade(
        pnl_state: IPnlState,
        trade: ITrade,
        create_pnl_state: CreatePnlState,
        create_partial_trade: CreatePartialTrade,
        push_unmatched: PushUnmatched,
        pop_unmatched: PopUnmatched,
        push_matched: PushMatched,
) -> IPnlState:
    return add_partial_trade(
        pnl_state,
        create_partial_trade(trade, trade.quantity),
        create_pnl_state,
        create_partial_trade,
        push_unmatched,
        pop_unmatched,
        push_matched
    )
