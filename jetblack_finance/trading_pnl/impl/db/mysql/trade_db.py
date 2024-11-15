"""A basic database implementation"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pymysql import Connection

from .... import TradingPnl, add_trade

from .market_trade import MarketTrade
from .pools import MatchedPool, UnmatchedPool
from .sql import create_tables, drop_tables, save_pnl, select_pnl, ensure_pnl


def _to_decimal(number: int | Decimal) -> Decimal:
    return number if isinstance(number, Decimal) else Decimal(number)


class TradeDb:

    def __init__(self, con: Connection) -> None:
        self._con = con
        self._pnl: dict[tuple[str, str], TradingPnl] = {}

    def add_trade(
        self,
        timestamp: datetime,
        ticker: str,
        quantity: int | Decimal,
        price: int | Decimal,
        book: str
    ) -> TradingPnl:
        with self._con.cursor() as cur:
            ensure_pnl(cur, ticker, book, timestamp)

            matched = MatchedPool(cur, ticker, book)
            unmatched = UnmatchedPool.Fifo(cur, ticker, book)
            pnl = select_pnl(cur, ticker, book, timestamp)

            trade = MarketTrade.create(
                cur,
                timestamp,
                ticker,
                _to_decimal(quantity),
                _to_decimal(price),
                book
            )
            pnl = add_trade(pnl, trade, unmatched, matched)
            save_pnl(cur, pnl, ticker, book, timestamp)
            self._con.commit()
            return pnl

    def create_tables(self) -> None:
        with self._con.cursor() as cur:
            create_tables(cur)

    def drop(self) -> None:
        with self._con.cursor() as cur:
            drop_tables(cur)
