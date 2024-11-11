"""The strip of P&L values"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple

class PnlStrip(NamedTuple):
    quantity: Decimal
    avg_cost: Decimal
    price: Decimal
    realized: Decimal
    unrealized: Decimal
