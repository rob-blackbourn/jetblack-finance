"""Types"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple, Tuple


class Trade(NamedTuple):
    """A simple trade"""

    quantity: Decimal
    """The signed quantity where a positive value is a buy"""

    price: Decimal
    """The price"""

    def split(self, quantity: Decimal) -> Tuple[Trade, Trade]:
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
    quantity: Decimal
    avg_cost: Decimal
    price: Decimal
    realized: Decimal
    unrealized: Decimal
