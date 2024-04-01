"""A scaled trade"""

from __future__ import annotations

from abc import abstractmethod
from decimal import Decimal
from typing import Literal, Tuple, Optional, Protocol


from .itrade import ITrade


class ISplitTrade(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...

    @property
    def trade(self) -> ITrade:
        ...

    @abstractmethod
    def split(self, quantity: Decimal) -> Tuple[ISplitTrade, ISplitTrade]:
        ...

    @abstractmethod
    def __neg__(self) -> ISplitTrade:
        ...


class SplitTrade(ISplitTrade):

    def __init__(
            self,
            trade: ITrade,
            used: Optional[Decimal] = None,
            sign: Literal[1, -1] = 1
    ) -> None:
        self._trade = trade
        self._used: Decimal = (
            used
            if used is not None
            else Decimal(0)
        )
        self._sign = sign

    @property
    def quantity(self) -> Decimal:
        return self._trade.quantity * self._sign - self._used

    @property
    def price(self) -> Decimal:
        return self._trade.price

    @property
    def trade(self) -> ITrade:
        return self._trade

    def split(self, quantity: Decimal) -> Tuple[SplitTrade, SplitTrade]:
        assert abs(self.quantity) >= abs(quantity)
        unused = self.quantity - quantity
        matched = SplitTrade(self._trade, self._used + unused, self._sign)
        unmatched = SplitTrade(self._trade, self._used + quantity, self._sign)
        return matched, unmatched

    def __neg__(self) -> SplitTrade:
        return SplitTrade(
            self._trade,
            self._used,
            1 if self._sign == -1 else -1
        )

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, SplitTrade) and
            self._trade == value._trade and
            self._used == value._used and
            self._sign == value._sign
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity * self._sign}) @ {self.price}"
