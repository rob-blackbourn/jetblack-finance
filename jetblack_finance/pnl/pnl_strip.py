"""Types"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple, Union

from .scaled_order import ScaledOrder


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: ScaledOrder
    """The opening trade"""

    closing: ScaledOrder
    """The closing trade"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized: Decimal
    unrealized: Decimal
