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


class PnlTrade(NamedTuple):
    quantity: Decimal
    trade: IMarketTrade


class IUnmatchedPool(Protocol):

    @abstractmethod
    def push(self, pnl_trade: PnlTrade) -> None:
        ...

    @abstractmethod
    def pop(self, quantity: Decimal, cost: Decimal) -> PnlTrade:
        ...

    def __len__(self) -> int:
        ...


class IMatchedPool(Protocol):

    @abstractmethod
    def push(self, opening: PnlTrade, closing: PnlTrade) -> None:
        ...

    def __len__(self) -> int:
        ...


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Decimal
    realized: Decimal
    unrealized: Decimal


class TradingPnl(NamedTuple):
    quantity: Decimal
    cost: Decimal
    realized: Decimal

    @property
    def avg_cost(self) -> Decimal:
        return Decimal(0) if self.quantity == 0 else -self.cost / self.quantity

    def unrealized(self, price: Decimal | int) -> Decimal:
        return self.quantity * price + self.cost

    def strip(self, price: Decimal | int) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            Decimal(price),
            self.realized,
            self.unrealized(price)
        )
