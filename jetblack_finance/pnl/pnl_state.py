"""A class representing the state of the P&L calculation"""

from decimal import Decimal
from typing import Protocol, Sequence

from .split_trade import ISplitTrade


class IPnlState(Protocol):
    quantity: Decimal
    cost: Decimal
    realized: Decimal
    unmatched: Sequence[ISplitTrade]
    matched: Sequence[tuple[ISplitTrade, ISplitTrade]]


class PnlState:

    def __init__(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[ISplitTrade],
            matched: Sequence[tuple[ISplitTrade, ISplitTrade]]
    ) -> None:
        self.quantity = quantity
        self.cost = cost
        self.realized = realized
        self.unmatched = unmatched
        self.matched = matched

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"
