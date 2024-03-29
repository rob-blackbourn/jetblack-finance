"""Types"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Tuple, Union, Optional


from .iorder import IOrder


class ScaledOrder:

    def __init__(
            self,
            trade: IOrder,
            scale: Optional[Fraction] = None
    ) -> None:
        self._trade = trade
        self._scale: Fraction = (
            scale
            if scale is not None
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
    def trade(self) -> IOrder:
        return self._trade

    def split(self, quantity: Decimal) -> Tuple[ScaledOrder, ScaledOrder]:
        if abs(quantity) > abs(self.quantity):
            raise ValueError("invalid quantity")
        remainder = self.quantity - quantity
        denominator = Fraction(self._trade.quantity)
        matched = ScaledOrder(self._trade, Fraction(quantity) / denominator)
        unmatched = ScaledOrder(self._trade, Fraction(remainder) / denominator)
        return matched, unmatched

    def __neg__(self) -> ScaledOrder:
        return ScaledOrder(self._trade, -self._scale)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, ScaledOrder) and
            self._trade == value._trade and
            self._scale == value._scale
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.price}"
