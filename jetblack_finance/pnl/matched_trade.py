"""MatchedTrade"""

from __future__ import annotations

from typing import NamedTuple

from .scaled_trade import ScaledTrade


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: ScaledTrade
    """The opening trade"""

    closing: ScaledTrade
    """The closing trade"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"
