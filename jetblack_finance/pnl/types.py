"""Types"""

from enum import Enum, auto
from typing import NamedTuple


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
