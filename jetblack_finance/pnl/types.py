"""Types"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from decimal import Decimal
from typing import NamedTuple, Tuple, Union


class ATrade(metaclass=ABCMeta):

    @property
    @abstractmethod
    def quantity(self) -> Decimal:
        ...

    @property
    @abstractmethod
    def price(self) -> Decimal:
        ...

    @abstractmethod
    def make_trade(self, quantity: Decimal) -> ATrade:
        ...

    def split(self, quantity: Decimal) -> Tuple[ATrade, ATrade]:
        matched = self.make_trade(quantity)
        unmatched = self.make_trade(self.quantity - quantity)
        return matched, unmatched


class MatchedTrade(NamedTuple):
    """A matched trade"""

    opening: ATrade
    """The opening trade"""

    closing: ATrade
    """The closing trade"""


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized: Decimal
    unrealized: Decimal
