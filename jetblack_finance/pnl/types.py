"""Common types
"""

from abc import abstractmethod
from decimal import Decimal
from typing import NamedTuple, Protocol, runtime_checkable


@runtime_checkable
class IMarketTrade(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...


class IPnlTrade(NamedTuple):
    quantity: Decimal
    trade: IMarketTrade


class IUnmatchedPool(Protocol):

    @abstractmethod
    def push(self, pnl_trade: IPnlTrade) -> None:
        ...

    @abstractmethod
    def pop(self, quantity: Decimal, cost: Decimal) -> IPnlTrade:
        ...

    def __len__(self) -> int:
        ...


class IMatchedPool(Protocol):

    @abstractmethod
    def push(self, opening: IPnlTrade, closing: IPnlTrade) -> None:
        ...

    def __len__(self) -> int:
        ...


class IPnlState(NamedTuple):
    quantity: Decimal
    cost: Decimal
    realized: Decimal
