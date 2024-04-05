"""ITrade"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol, Union, runtime_checkable

Number = Union[Decimal, int]


@runtime_checkable
class ITrade(Protocol):

    quantity: Decimal
    price: Decimal


def _to_decimal(number: Number) -> Decimal:
    if isinstance(number, Decimal):
        return number
    return Decimal(number)


class Trade(ITrade):
    """A simple trade"""

    def __init__(self, quantity: Number, price: Number) -> None:
        self.quantity = _to_decimal(quantity)
        self.price = _to_decimal(price)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Trade) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"
