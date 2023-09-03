"""Types"""

from __future__ import annotations

from typing import NamedTuple, Tuple


class Trade(NamedTuple):
    """A simple trade"""

    quantity: int
    """The signed quantity where a positive value is a buy"""

    price: float
    """The price"""

    def split(self, quantity: int) -> Tuple[Trade, Trade]:
        matched = Trade(quantity, self.price)
        unmatched = Trade(self.quantity-quantity, self.price)
        return matched, unmatched


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: Trade
    """The opening trade"""

    closing: Trade
    """The closing trade"""


class PnlStrip(NamedTuple):
    quantity: int
    avg_cost: float
    price: float
    realized: float
    unrealized: float
