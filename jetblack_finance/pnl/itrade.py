"""IOrder"""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol

from .iorder import IOrder
from .isecurity import ISecurity


class ITrade(Protocol):

    @property
    @abstractmethod
    def security(self) -> ISecurity:
        ...

    @property
    @abstractmethod
    def order(self) -> IOrder:
        ...
