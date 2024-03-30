"""A scaled order"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Tuple, Optional


from .iorder import IOrder


class ScaledOrder:

    def __init__(
            self,
            order: IOrder,
            scale: Optional[Fraction] = None
    ) -> None:
        self._order = order
        self._scale: Fraction = (
            scale
            if scale is not None
            else Fraction(1)
        )
        if self._scale > 1:
            raise ValueError(f"invalid scale '{self._scale}'")

    @property
    def quantity(self) -> Decimal:
        quantity = Fraction(self._order.quantity) * self._scale
        return Decimal(quantity.numerator) / Decimal(quantity.denominator)

    @property
    def price(self) -> Decimal:
        return self._order.price

    @property
    def order(self) -> IOrder:
        return self._order

    def split(self, quantity: Decimal) -> Tuple[ScaledOrder, ScaledOrder]:
        if abs(quantity) > abs(self.quantity):
            raise ValueError("invalid quantity")
        remainder = self.quantity - quantity
        denominator = Fraction(self._order.quantity)
        matched = ScaledOrder(self._order, Fraction(quantity) / denominator)
        unmatched = ScaledOrder(self._order, Fraction(remainder) / denominator)
        return matched, unmatched

    def __neg__(self) -> ScaledOrder:
        return ScaledOrder(
            self._order,
            -self._scale  # pylint: disable=invalid-unary-operand-type
        )

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, ScaledOrder) and
            self._order == value._order and
            self._scale == value._scale
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._order.quantity}) @ {self.price}"
