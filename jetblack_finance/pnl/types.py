"""Common types
"""

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol, runtime_checkable


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


class IPartialTrade(Protocol):

    @property
    @abstractmethod
    def trade(self) -> IMarketTrade:
        ...

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...


class IUnmatchedPool(Protocol):

    @abstractmethod
    def push(self, partial_trade: IPartialTrade) -> None:
        ...

    @abstractmethod
    def pop(self, quantity: Decimal, cost: Decimal) -> IPartialTrade:
        ...

    def __len__(self) -> int:
        ...


class IMatchedPool(Protocol):

    @abstractmethod
    def push(self, opening: IPartialTrade, closing: IPartialTrade) -> None:
        ...

    def __len__(self) -> int:
        ...


class IPnlState(Protocol):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def cost(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def realized(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def unmatched(self) -> IUnmatchedPool:
        ...

    @property
    @abstractmethod
    def matched(self) -> IMatchedPool:
        ...
