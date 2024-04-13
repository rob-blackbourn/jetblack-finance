"""A class representing the state of the P&L calculation"""

from decimal import Decimal
from typing import Sequence, Tuple

from .split_trade import ISplitTrade


class PnlState:

    def __init__(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: Sequence[ISplitTrade],
            matched: Sequence[Tuple[ISplitTrade, ISplitTrade]]
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
    def unmatched(self) -> Sequence[ISplitTrade]:
        return self._unmatched

    @property
    def matched(self) -> Sequence[Tuple[ISplitTrade, ISplitTrade]]:
        return self._matched

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"
