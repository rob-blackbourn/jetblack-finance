"""ITrade"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class ITrade(Protocol):

    @property
    def quantity(self) -> Decimal:
        ...

    @property
    def price(self) -> Decimal:
        ...

    def make_trade(self, quantity: Decimal) -> ITrade:
        ...
