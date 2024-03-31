"""A scaled order"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Tuple, Optional


from .iorder import IOrder


class SplitOrder:

    def __init__(
            self,
            order: IOrder,
            used: Optional[Decimal] = None,
            sign: Literal[1, -1] = 1
    ) -> None:
        self._order = order
        self._used: Decimal = (
            used
            if used is not None
            else Decimal(0)
        )
        self._sign = sign

    @property
    def quantity(self) -> Decimal:
        return self._order.quantity * self._sign - self._used

    @property
    def price(self) -> Decimal:
        return self._order.price

    @property
    def order(self) -> IOrder:
        return self._order

    def split(self, quantity: Decimal) -> Tuple[SplitOrder, SplitOrder]:
        assert abs(self.quantity) >= abs(quantity)
        unused = self.quantity - quantity
        matched = SplitOrder(self._order, self._used + unused, self._sign)
        unmatched = SplitOrder(self._order, self._used + quantity, self._sign)
        return matched, unmatched

    def __neg__(self) -> SplitOrder:
        return SplitOrder(
            self._order,
            self._used,
            1 if self._sign == -1 else -1
        )

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, SplitOrder) and
            self._order == value._order and
            self._used == value._used and
            self._sign == value._sign
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._order.quantity * self._sign}) @ {self.price}"
