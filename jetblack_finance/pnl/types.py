"""Types"""

from typing import NamedTuple


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
