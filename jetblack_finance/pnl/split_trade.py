"""A scaled trade"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Tuple, Optional, Protocol


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
    def split(self, quantity: Decimal) -> Tuple[ISplitTrade, ISplitTrade]:
        ...


class SplitTrade(ISplitTrade):

    def __init__(
            self,
            trade: ITrade,
            used: Optional[Decimal] = None,
    ) -> None:
        self._trade = trade
        self._used: Decimal = (
            used
            if used is not None
            else Decimal(0)
        )

    @property
    def quantity(self) -> Decimal:
        return self._trade.quantity - self._used

    @property
    def price(self) -> Decimal:
        return self._trade.price

    def split(self, quantity: Decimal) -> Tuple[SplitTrade, SplitTrade]:
        assert abs(self.quantity) >= abs(quantity)
        unused = self.quantity - quantity
        matched = SplitTrade(self._trade, self._used + unused)
        unmatched = SplitTrade(self._trade, self._used + quantity)
        return matched, unmatched

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, SplitTrade) and
            self._trade == value._trade and
            self._used == value._used
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.price}"
