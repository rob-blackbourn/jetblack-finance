"""ITrade"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol, Union, runtime_checkable

Number = Union[Decimal, int]


@runtime_checkable
class ITrade(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...


def _to_decimal(number: Number) -> Decimal:
    if isinstance(number, Decimal):
        return number
    return Decimal(number)


class Trade(ITrade):
    """A simple trade"""

    def __init__(self, quantity: Number, price: Number) -> None:
        self._quantity = _to_decimal(quantity)
        self._price = _to_decimal(price)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Trade) and
            value.quantity == self.quantity and
            value.price == self.price
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.price}"
