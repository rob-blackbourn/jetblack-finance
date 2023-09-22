"""Types"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple, Union


class TradePnlStrip(NamedTuple):
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    price: Union[Decimal, int]
    realized_quote_ccy: Decimal
    unrealized_quote_ccy: Decimal
    quote_ccy: str
    realized_base_ccy: Decimal
    unrealized_base_ccy: Decimal
    base_ccy: str
