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


class ScaledTrade:

    def __init__(
            self,
            trade: ITrade,
            quantity: Optional[Union[Decimal, int]] = None
    ) -> None:
        self._trade = trade
        self._scale = (
            Fraction(quantity) / Fraction(trade.quantity)
            if quantity is not None
            else Fraction(1)
        )
        if self._scale > 1:
            raise ValueError(f"invalid scale '{self._scale}'")

    @property
    def quantity(self) -> Decimal:
        quantity = Fraction(self._trade.quantity) * self._scale
        return Decimal(quantity.numerator) / Decimal(quantity.denominator)

    @property
    def price(self) -> Decimal:
        return self._trade.price

    @property
    def trade(self) -> ITrade:
        return self._trade

    def split(self, quantity: Decimal) -> Tuple[ScaledTrade, ScaledTrade]:
        if abs(quantity) > abs(self.quantity):
            raise ValueError("invalid quantity")
        matched = ScaledTrade(self._trade, quantity)
        unmatched = ScaledTrade(self._trade, self.quantity - quantity)
        return matched, unmatched

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, ScaledTrade) and
            self._trade == value._trade and
            self._scale == value._scale
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.trade.price}"


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: ScaledTrade
    """The opening trade"""

    closing: ScaledTrade
    """The closing trade"""

    def __repr__(self) -> str:
        return f"{self.opening!r} / {self.closing!r}"


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized: Decimal
    unrealized: Decimal
