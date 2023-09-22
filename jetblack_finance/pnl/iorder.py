"""IOrder"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol


class IOrder(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...

    @abstractmethod
    def make_order(self, quantity: Decimal) -> IOrder:
        ...
