"""Types"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple, Protocol, Tuple, Union, cast


class ITrade(Protocol):

    @property
    def quantity(self) -> Decimal:
        ...

    @property
    def price(self) -> Decimal:
        ...

    def make_trade(self, quantity: Decimal) -> ITrade:
        ...


class UnmatchedTrade:

    def __init__(self, trade: ITrade, version: int) -> None:
        self._trade = trade
        self._version = version

    @property
    def quantity(self) -> Decimal:
        return self._trade.quantity

    @property
    def price(self) -> Decimal:
        return self._trade.price

    @property
    def trade(self) -> ITrade:
        return self._trade

    def split(self, quantity: Decimal) -> Tuple[UnmatchedTrade, UnmatchedTrade]:
        matched = cast(ITrade, self._trade.make_trade(quantity))
        unmatched = cast(ITrade, self._trade.make_trade(
            self.quantity - quantity))
        return (
            UnmatchedTrade(matched, self._version),
            UnmatchedTrade(unmatched, self._version + 1)
        )

    def __eq__(self, value: object) -> bool:
        return isinstance(value, UnmatchedTrade) and self._trade == self._trade


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: UnmatchedTrade
    """The opening trade"""

    closing: UnmatchedTrade
    """The closing trade"""


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized: Decimal
    unrealized: Decimal
