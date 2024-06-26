"""A scaled trade"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol


from .trade import ITrade


class ISplitTrade(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...

    @abstractmethod
    def split(self, quantity: Decimal) -> tuple[ISplitTrade, ISplitTrade]:
        ...


class SplitTrade(ISplitTrade):

    def __init__(
            self,
            trade: ITrade,
            quantity: Decimal | None = None,
    ) -> None:
        self._trade = trade
        self._quantity: Decimal = (
            quantity
            if quantity is not None
            else trade.quantity
        )

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._trade.price

    def split(self, quantity: Decimal) -> tuple[SplitTrade, SplitTrade]:
        assert abs(self.quantity) >= abs(quantity)
        matched = SplitTrade(self._trade, quantity)
        unmatched = SplitTrade(self._trade, self.quantity - quantity)
        return matched, unmatched

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, SplitTrade) and
            self._trade == value._trade and
            self.quantity == value.quantity
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.price}"
