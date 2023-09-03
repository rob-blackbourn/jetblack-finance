"""A calculator for trading P&L"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import deque
from decimal import Decimal
from typing import Deque, List, Optional, Tuple, Union

from .types import (
    MatchedTrade,
    ATrade,
    PnlStrip
)


class TradingPnl(metaclass=ABCMeta):
    """A class to calculate trading P&L"""

    def __init__(self) -> None:
        self.quantity: Decimal = Decimal(0)
        self.cost: Decimal = Decimal(0)
        self.realized: Decimal = Decimal(0)
        self.unmatched: Deque[ATrade] = deque()
        self.matched: List[MatchedTrade] = []

    def add(self, trade: ATrade) -> None:
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
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)

        return -self.cost / self.quantity

    def unrealized(self, price: Union[Decimal, int]) -> Decimal:
        return self.quantity * price + self.cost

    def pnl(self, price: Union[Decimal, int]) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            price,
            self.realized,
            self.unrealized(price)
        )

    def _extend_position(self, trade: ATrade) -> None:
        self.cost -= trade.quantity * trade.price
        self.quantity += trade.quantity
        self.unmatched.append(trade)

    def _match(self, trade_candidate: ATrade) -> Tuple[ATrade, ATrade, Optional[ATrade]]:
        match_candidate = self.pop_unmatched()

        if abs(trade_candidate.quantity) >= abs(match_candidate.quantity):
            # Split the candidate trade to match the quantity. This leaves a
            # remaining trade to match.
            trade, remaining_trade = trade_candidate.split(
                -match_candidate.quantity
            )
            # The matching trade is the whole of the candidate.
            match = match_candidate
        else:
            # The trade is the entire candidate trade. There is no remaining
            # trade.
            trade, remaining_trade = trade_candidate, None
            # Split the candidate match by the smaller trade quantity, and
            # return the remaining unmatched.
            match, remaining_unmatched = match_candidate.split(
                -trade_candidate.quantity
            )
            self.push_unmatched(remaining_unmatched)

        return trade, match, remaining_trade

    def _reduce_position(self, trade: Optional[ATrade]) -> None:
        while trade is not None and trade.quantity != 0 and self.unmatched:
            trade, match, remaining_trade = self._match(trade)

            trade_cost = -(trade.quantity * trade.price)
            match_cost = -(match.quantity * match.price)

            self.realized += trade_cost + match_cost
            self.cost -= match_cost
            self.quantity += trade.quantity

            self.matched.append(MatchedTrade(match, trade))

            trade = remaining_trade

        if trade is not None and trade.quantity != 0:
            self.add(trade)

    @abstractmethod
    def pop_unmatched(self) -> ATrade:
        ...

    @abstractmethod
    def push_unmatched(self, trade: ATrade) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.quantity} {self.cost} {self.realized}"


class FifoTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ATrade:
        return self.unmatched.popleft()

    def push_unmatched(self, trade: ATrade) -> None:
        self.unmatched.appendleft(trade)


class LifoTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ATrade:
        return self.unmatched.pop()

    def push_unmatched(self, trade: ATrade) -> None:
        self.unmatched.append(trade)


class BestPriceTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ATrade:
        trades = sorted(self.unmatched, key=lambda x: x.price)
        trade = trades[0] if self.quantity > 0 else trades[-1]
        self.unmatched.remove(trade)
        return trade

    def push_unmatched(self, trade: ATrade) -> None:
        self.unmatched.append(trade)


class WorstPriceTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ATrade:
        trades = sorted(self.unmatched, key=lambda x: x.price)
        trade = trades[-1] if self.quantity > 0 else trades[0]
        self.unmatched.remove(trade)
        return trade

    def push_unmatched(self, trade: ATrade) -> None:
        self.unmatched.append(trade)
