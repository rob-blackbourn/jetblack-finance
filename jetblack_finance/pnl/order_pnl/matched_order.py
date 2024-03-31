"""MatchedOrder"""

from __future__ import annotations

from typing import NamedTuple

from .split_order import SplitOrder


class MatchedOrder(NamedTuple):
    """A matched order"""

    opening: SplitOrder
    """The opening order"""

    closing: SplitOrder
    """The closing order"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"
