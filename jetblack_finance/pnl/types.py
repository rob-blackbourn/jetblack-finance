"""Types"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import NamedTuple, Protocol, Tuple, Union, Optional


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

    def __init__(self, trade: ITrade, quantity: Optional[Union[Decimal, int]] = None) -> None:
        self._trade = trade
        self._fraction = (
            Fraction(quantity) / Fraction(trade.quantity)
            if quantity is not None
            else Fraction(1)
        )

    @property
    def quantity(self) -> Decimal:
        quantity = Fraction(self._trade.quantity) * self._fraction
        return Decimal(quantity.numerator) / Decimal(quantity.denominator)

    @property
    def price(self) -> Decimal:
        return self._trade.price

    @property
    def trade(self) -> ITrade:
        return self._trade

    def split(self, quantity: Decimal) -> Tuple[UnmatchedTrade, UnmatchedTrade]:
        if abs(quantity) > abs(self.quantity):
            raise ValueError("invalid quantity")
        matched = UnmatchedTrade(self._trade, quantity)
        unmatched = UnmatchedTrade(self._trade, self.quantity - quantity)
        return matched, unmatched

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, UnmatchedTrade) and
            self._trade == value._trade and
            self._fraction == value._fraction
        )

    def __repr__(self) -> str:
        return f"{self.quantity} of {self._trade.quantity} @ {self.trade.price}"


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: UnmatchedTrade
    """The opening trade"""

    closing: UnmatchedTrade
    """The closing trade"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized: Decimal
    unrealized: Decimal
