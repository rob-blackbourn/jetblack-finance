"""Utilities for P/L tests"""

from decimal import Decimal
from typing import Union

from jetblack_finance.pnl import IOrder

Number = Union[Decimal, int]


def _to_decimal(number: Number) -> Decimal:
    if isinstance(number, Decimal):
        return number
    return Decimal(number)


class Order(IOrder):
    """A simple order"""

    def __init__(self, quantity: Number, price: Number) -> None:
        self._quantity = _to_decimal(quantity)
        self._price = _to_decimal(price)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    def make_order(self, quantity: Decimal) -> IOrder:
        return Order(quantity, self.price)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Order) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"
