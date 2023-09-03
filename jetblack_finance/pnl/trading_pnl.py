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

    def add(self, trade: Trade) -> None:
        if (
            # We are flat
            self.quantity == 0 or
            # We are long and buying
            (self.quantity > 0 and trade.quantity > 0) or
            # We are short and selling.
            (self.quantity < 0 and trade.quantity < 0)
        ):
            self._extend_position(trade)
        else:
            self._reduce_position(trade)

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

    def _extend_position(self, trade: Trade) -> None:
        self.cost -= trade.quantity * trade.price
        self.quantity += trade.quantity
        self.unmatched.append(trade)

    def _reduce_position(self, trade: Trade) -> None:
        while self.unmatched and trade.quantity != 0:
            matched = self.pop_unmatched()

            if abs(matched.quantity) <= abs(trade.quantity):
                trade, next_trade = trade.split(-matched.quantity)
            else:
                matched, unmatched = matched.split(-trade.quantity)
                self.push_unmatched(unmatched)
                next_trade = Trade(0, 0)

            trade_cost = -trade.quantity * trade.price
            matched_cost = -matched.quantity * matched.price

            self.realized += trade_cost + matched_cost
            self.cost -= matched_cost
            self.quantity += trade.quantity

            self.matched.append(MatchedTrade(matched, trade))

            trade = next_trade

        if trade.quantity != 0:
            self.add(trade)

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
