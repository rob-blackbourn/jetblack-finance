"""MatchedTrade"""

from __future__ import annotations

from typing import NamedTuple

from .split_trade import ISplitTrade


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: ISplitTrade
    """The opening trade"""

    closing: ISplitTrade
    """The closing trade"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"
