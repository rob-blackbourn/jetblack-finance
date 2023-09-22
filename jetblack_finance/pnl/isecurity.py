"""ISecurity"""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol


class ISecurity(Protocol):

    @property
    @abstractmethod
    def symbol(self) -> str:
        ...

    @property
    @abstractmethod
    def ccy(self) -> str:
        ...
