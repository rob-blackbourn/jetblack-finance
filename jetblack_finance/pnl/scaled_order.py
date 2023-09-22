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
    def trade(self) -> IOrder:
        return self._trade

    def split(self, quantity: Decimal) -> Tuple[ScaledOrder, ScaledOrder]:
        if abs(quantity) > abs(self.quantity):
            raise ValueError("invalid quantity")
        matched = ScaledOrder(self._trade, quantity)
        unmatched = ScaledOrder(self._trade, self.quantity - quantity)
        return matched, unmatched

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, ScaledOrder) and
            self._trade == value._trade and
            self._scale == value._scale
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.trade.price}"
