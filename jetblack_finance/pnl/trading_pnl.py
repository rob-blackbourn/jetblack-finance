"""A calculator for trading P&L"""

from __future__ import annotations

from collections import deque
from enum import Enum, auto
from typing import Deque, List, Literal, NamedTuple, Tuple


class MatchStyle(Enum):
    """How to choose a trade to match against"""

    FIFO = auto()
    """First in first out - take the oldest"""

    LIFO = auto()
    """Last in last out - take the newest"""

    BEST_PRICE = auto()
    """When long take the lowest price, when short take the highest"""

    WORST_PRICE = auto()
    """When long take the highest price, when short take the lowest"""


class Trade(NamedTuple):
    """A simple trade"""

    quantity: int
    """The signed quantity where a positive value is a buy"""

    price: float
    """The price"""


class MatchedTrade(NamedTuple):
    """A matched trade"""

    quantity: int
    """The quantity with the sign of the closing trade"""

    opening_price: float
    """The price of the opening trade"""

    closing_price: float
    """The price of the closing trade"""


class PnlStrip(NamedTuple):
    quantity: int
    avg_cost: float
    price: float
    realized: float
    unrealized: float


class TradingPnl:
    """A class to calculate trading P&L"""

    def __init__(self) -> None:
        self.quantity: int = 0
        self.cost: float = 0
        self.realized: float = 0
        self.unmatched: Deque[Trade] = deque()
        self.matched: List[MatchedTrade] = []

    def add(
            self,
            quantity: int,
            price: float,
            match_style: MatchStyle = MatchStyle.BEST_PRICE
    ) -> None:
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
            self._reduce_position(quantity, price, match_style)

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

    def _reduce_position(
            self,
            quantity: int,
            price: float,
            match_style: MatchStyle
    ) -> None:
        while self.unmatched and quantity != 0:
            matched_quantity, matched_price = self._pop_unmatched(match_style)

            if abs(matched_quantity) <= abs(quantity):
                remaining_quantity = quantity + matched_quantity
                quantity = -matched_quantity
            else:
                unmatched_quantity = matched_quantity + quantity
                matched_quantity = -quantity
                self._push_unmatched(
                    Trade(unmatched_quantity, matched_price),
                    match_style
                )
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
            self.add(quantity, price, match_style)

    def _pop_unmatched(self, match_style: MatchStyle) -> Trade:
        if match_style == MatchStyle.FIFO:
            return self.unmatched.popleft()

        if match_style == MatchStyle.LIFO:
            return self.unmatched.pop()

        trades = sorted(self.unmatched, key=lambda x: x[1])

        if match_style == MatchStyle.BEST_PRICE:
            trade = trades[-1] if self.quantity > 0 else trades[0]
        elif match_style == MatchStyle.WORST_PRICE:
            trade = trades[0] if self.quantity > 0 else trades[-1]
        else:
            raise ValueError("unknown match style")

        self.unmatched.remove(trade)

        return trade

    def _push_unmatched(self, trade: Trade, match_style: MatchStyle) -> None:
        if match_style == MatchStyle.FIFO:
            self.unmatched.appendleft(trade)
        elif match_style == MatchStyle.LIFO:
            self.unmatched.append(trade)
        elif match_style in (MatchStyle.BEST_PRICE, MatchStyle.WORST_PRICE):
            self.unmatched.append(trade)
        else:
            raise ValueError("unknown match style")

    def __repr__(self) -> str:
        return f"{self.quantity} {self.cost} {self.realized}"
