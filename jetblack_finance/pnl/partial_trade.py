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

class PartialTrade(IPartialTrade):

    def __init__(
            self,
            trade: ITrade,
            quantity: Decimal
    ) -> None:
        self._trade = trade
        self._quantity = quantity

    @property
    def trade(self) -> ITrade:
        return self._trade

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._trade.price

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, PartialTrade) and
            self._trade == value._trade and
            self.quantity == value.quantity
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.price}"
