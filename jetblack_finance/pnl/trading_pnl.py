"""A calculator for trading P&L"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections import deque
from decimal import Decimal
from typing import Deque, List, Optional, Tuple, Union

from .types import (
    MatchedTrade,
    ITrade,
    ScaledTrade,
    PnlStrip
)


class TradingPnl(metaclass=ABCMeta):
    """A class to calculate trading P&L"""

    def __init__(self) -> None:
        self.quantity: Decimal = Decimal(0)
        self.cost: Decimal = Decimal(0)
        self.realized: Decimal = Decimal(0)
        self.unmatched: Deque[ScaledTrade] = deque()
        self.matched: List[MatchedTrade] = []

    def add(self, trade: ITrade) -> None:
        self._add(ScaledTrade(trade))

    def _add(self, trade: ScaledTrade) -> None:
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

    def _extend_position(self, trade: ScaledTrade) -> None:
        self.cost -= trade.quantity * trade.price
        self.quantity += trade.quantity
        self.unmatched.append(trade)

    def _find_match(
            self,
            trade_candidate: ScaledTrade
    ) -> Tuple[ScaledTrade, ScaledTrade, Optional[ScaledTrade]]:
        match_candidate = self.pop_unmatched()

        if abs(trade_candidate.quantity) >= abs(match_candidate.quantity):
            # Split the candidate trade to match the quantity. This leaves a
            # remaining trade to match.
            close_trade, trade = trade_candidate.split(
                -match_candidate.quantity
            )
            # The matching trade is the whole of the candidate.
            open_trade = match_candidate
        else:
            # The trade is the entire candidate trade. There is no remaining
            # trade.
            close_trade, trade = trade_candidate, None
            # Split the candidate match by the smaller trade quantity, and
            # return the remaining unmatched.
            open_trade, remaining_unmatched = match_candidate.split(
                -trade_candidate.quantity
            )
            self.push_unmatched(remaining_unmatched)

        return close_trade, open_trade, trade

    def _match(self, trade: ScaledTrade) -> Optional[ScaledTrade]:
        close_trade, open_trade, remainder = self._find_match(trade)

        # Note that the open will have the opposite sign to the close.
        close_value = close_trade.quantity * close_trade.price
        open_cost = -(open_trade.quantity * open_trade.price)

        # The difference between the two costs is the realised value.
        self.realized -= close_value - open_cost
        # Remove the cost.
        self.cost -= open_cost
        # Remove the quantity.
        self.quantity -= open_trade.quantity

        self.matched.append(MatchedTrade(open_trade, close_trade))

        return remainder

    def _reduce_position(self, trade: Optional[ScaledTrade]) -> None:
        while trade is not None and trade.quantity != 0 and self.unmatched:
            trade = self._match(trade)

        if trade is not None and trade.quantity != 0:
            self._add(trade)

    @abstractmethod
    def pop_unmatched(self) -> ScaledTrade:
        ...

    @abstractmethod
    def push_unmatched(self, trade: ScaledTrade) -> None:
        ...

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


class FifoTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ScaledTrade:
        return self.unmatched.popleft()

    def push_unmatched(self, trade: ScaledTrade) -> None:
        self.unmatched.appendleft(trade)


class LifoTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ScaledTrade:
        return self.unmatched.pop()

    def push_unmatched(self, trade: ScaledTrade) -> None:
        self.unmatched.append(trade)


class BestPriceTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ScaledTrade:
        trades = sorted(self.unmatched, key=lambda x: x.price)
        trade = trades[0] if self.quantity > 0 else trades[-1]
        self.unmatched.remove(trade)
        return trade

    def push_unmatched(self, trade: ScaledTrade) -> None:
        self.unmatched.append(trade)


class WorstPriceTradingPnl(TradingPnl):

    def pop_unmatched(self) -> ScaledTrade:
        trades = sorted(self.unmatched, key=lambda x: x.price)
        trade = trades[-1] if self.quantity > 0 else trades[0]
        self.unmatched.remove(trade)
        return trade

    def push_unmatched(self, trade: ScaledTrade) -> None:
        self.unmatched.append(trade)
