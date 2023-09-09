"""ITrade"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol


class ITrade(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...

    @abstractmethod
    def make_trade(self, quantity: Decimal) -> ITrade:
        ...
