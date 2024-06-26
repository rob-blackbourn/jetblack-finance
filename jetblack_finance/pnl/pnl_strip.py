"""The strip of P&L values"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple, Union


class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized: Decimal
    unrealized: Decimal
