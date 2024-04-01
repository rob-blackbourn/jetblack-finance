"""A class representing the state of the P&L calculation"""

from decimal import Decimal
from typing import Sequence

from .matched_trade import MatchedTrade
from .split_trade import SplitTrade

Unmatched = Sequence[SplitTrade]
Matched = Sequence[MatchedTrade]


class PnlState:

    def __init__(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Unmatched,
            matched: Matched
    ) -> None:
        self._quantity = quantity
        self._cost = cost
        self._realized = realized
        self._unmatched = unmatched
        self._matched = matched

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

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"
