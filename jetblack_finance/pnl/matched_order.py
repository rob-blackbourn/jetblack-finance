"""MatchedTrade"""

from __future__ import annotations

from typing import NamedTuple

from .scaled_order import ScaledOrder


class MatchedOrder(NamedTuple):
    """A matched order"""

    opening: ScaledOrder
    """The opening order"""

    closing: ScaledOrder
    """The closing order"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"
