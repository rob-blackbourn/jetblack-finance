"""A class representing the state of the P&L calculation"""

from decimal import Decimal
from typing import Protocol, Sequence

from .partial_trade import IPartialTrade


class IPnlState(Protocol):
    quantity: Decimal
    cost: Decimal
    realized: Decimal
    unmatched: Sequence[IPartialTrade]
    matched: Sequence[tuple[IPartialTrade, IPartialTrade]]


class PnlState:

    def __init__(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[IPartialTrade],
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> None:
        self.quantity = quantity
        self.cost = cost
        self.realized = realized
        self.unmatched = unmatched
        self.matched = matched

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"
