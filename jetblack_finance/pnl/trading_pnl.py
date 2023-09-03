"""A calculator for trading P&L"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import deque
from typing import Deque, List

from .types import (
    MatchedTrade,
    Trade,
    PnlStrip
)


class TradingPnl(metaclass=ABCMeta):
    """A class to calculate trading P&L"""

    def __init__(self) -> None:
        self.quantity: int = 0
        self.cost: float = 0
        self.realized: float = 0
        self.unmatched: Deque[Trade] = deque()
        self.matched: List[MatchedTrade] = []

    def add(self, quantity: int, price: float) -> None:
        if (
            # We are flat
            self.quantity == 0 or
            # We are long and buying
            (self.quantity > 0 and quantity > 0) or
            # We are short and selling.
            (self.quantity < 0 and quantity < 0)
        ):
            self._extend_position(quantity, price)
        else:
            self._reduce_position(quantity, price)

    @property
    def avg_cost(self) -> float:
        if self.quantity == 0:
            return 0

        return -self.cost / self.quantity

    def unrealized(self, price: float) -> float:
        return self.quantity * price + self.cost

    def pnl(self, price: float) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            price,
            self.realized,
            self.unrealized(price)
        )

    def _extend_position(self, quantity: int, price: float) -> None:
        self.cost -= quantity * price
        self.quantity += quantity
        self.unmatched.append(Trade(quantity, price))

    def _reduce_position(self, quantity: int, price: float) -> None:
        while self.unmatched and quantity != 0:
            matched_quantity, matched_price = self.pop_unmatched()

            if abs(matched_quantity) <= abs(quantity):
                remaining_quantity = quantity + matched_quantity
                quantity = -matched_quantity
            else:
                unmatched_quantity = matched_quantity + quantity
                matched_quantity = -quantity
                self.push_unmatched(Trade(unmatched_quantity, matched_price))
                remaining_quantity = 0

            self.matched.append(
                MatchedTrade(quantity, matched_price, price)
            )

            matched_cost = -matched_quantity * matched_price
            trade_cost = -quantity * price

            self.quantity -= matched_quantity
            self.cost -= matched_cost
            self.realized += trade_cost + matched_cost

            quantity = remaining_quantity

        if quantity != 0:
            self.add(quantity, price)

    @abstractmethod
    def pop_unmatched(self) -> Trade:
        ...

    @abstractmethod
    def push_unmatched(self, trade: Trade) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.quantity} {self.cost} {self.realized}"


class FifoTradingPnl(TradingPnl):

    def pop_unmatched(self) -> Trade:
        return self.unmatched.popleft()

    def push_unmatched(self, trade: Trade) -> None:
        self.unmatched.appendleft(trade)


class LifoTradingPnl(TradingPnl):

    def pop_unmatched(self) -> Trade:
        return self.unmatched.pop()

    def push_unmatched(self, trade: Trade) -> None:
        self.unmatched.append(trade)


class BestPriceTradingPnl(TradingPnl):

    def pop_unmatched(self) -> Trade:
        trades = sorted(self.unmatched, key=lambda x: x[1])
        trade = trades[0] if self.quantity > 0 else trades[-1]
        self.unmatched.remove(trade)
        return trade

    def push_unmatched(self, trade: Trade) -> None:
        self.unmatched.append(trade)


class WorstPriceTradingPnl(TradingPnl):

    def pop_unmatched(self) -> Trade:
        trades = sorted(self.unmatched, key=lambda x: x[1])
        trade = trades[-1] if self.quantity > 0 else trades[0]
        self.unmatched.remove(trade)
        return trade

    def push_unmatched(self, trade: Trade) -> None:
        self.unmatched.append(trade)
