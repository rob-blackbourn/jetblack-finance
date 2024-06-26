"""A class representing the state of the P&L calculation"""

from abc import abstractmethod
from decimal import Decimal
from typing import Protocol, Sequence

from .partial_trade import IPartialTrade


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
    def unmatched(self) -> Sequence[IPartialTrade]:
        ...

    @property
    @abstractmethod
    def matched(self) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        ...
