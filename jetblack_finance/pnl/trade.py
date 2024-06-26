"""ITrade"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol, runtime_checkable


@runtime_checkable
class ITrade(Protocol):

    quantity: Decimal
    price: Decimal


class Trade(ITrade):
    """A simple trade"""

    def __init__(self, quantity: Decimal, price: Decimal) -> None:
        self.quantity = quantity
        self.price = price

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Trade) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"
