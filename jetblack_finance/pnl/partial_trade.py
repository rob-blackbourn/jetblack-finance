"""A partial trade"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol


from .trade import ITrade


class IPartialTrade(Protocol):

    @property
    @abstractmethod
    def trade(self) -> ITrade:
        ...

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...
