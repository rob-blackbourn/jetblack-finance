"""MatchedTrade"""

from __future__ import annotations

from typing import NamedTuple

from .split_trade import SplitTrade


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: SplitTrade
    """The opening trade"""

    closing: SplitTrade
    """The closing trade"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"
