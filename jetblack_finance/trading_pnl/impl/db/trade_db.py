"""A basic database implementation"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pymysql import Connection
from pymysql.cursors import Cursor

from ... import TradingPnl, add_trade

from .market_trade import MarketTrade
from .pools import MatchedPool, UnmatchedPool


def save_pnl_state(cur: Cursor, pnl: TradingPnl, ticker: str, book: str) -> None:
    cur.execute(
        """
        INSERT INTO trading.pnl
        (
            ticker,
            book,
            quantity,
            cost,
            realized
        ) VALUES (
            %(ticker)s,
            %(book)s,
            %(quantity)s,
            %(cost)s,
            %(realized)s
        ) ON DUPLICATE KEY UPDATE
            quantity = %(quantity)s,
            cost = %(cost)s,
            realized = %(realized)s
        """,
        {
            'ticker': ticker,
            'book': book,
            'quantity': pnl.quantity,
            'cost': pnl.cost,
            'realized': pnl.realized
        }
    )


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
            matched = MatchedPool(cur, ticker, book)
            unmatched = UnmatchedPool.Fifo(cur, ticker, book)
            pnl = self._pnl.get(
                (ticker, book),
                TradingPnl(Decimal(0), Decimal(0), Decimal(0))
            )

            trade = MarketTrade.create(
                cur,
                timestamp,
                ticker,
                _to_decimal(quantity),
                _to_decimal(price),
                book
            )
            pnl = add_trade(pnl, trade, unmatched, matched)
            save_pnl_state(cur, pnl, ticker, book)
            self._con.commit()
            return pnl

    def create_tables(self) -> None:
        with self._con.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trading.pnl
                (
                    ticker      VARCHAR(32)     NOT NULL,
                    book        VARCHAR(32)     NOT NULL,
                    quantity    DECIMAL(12, 0)  NOT NULL,
                    cost        DECIMAL(18, 6)  NOT NULL,
                    realized    DECIMAL(18, 6)  NOT NULL,

                    PRIMARY KEY(ticker, book)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trading.trade
                (
                    trade_id    INTEGER         NOT NULL AUTO_INCREMENT,
                    timestamp   TIMESTAMP       NOT NULL,
                    ticker      VARCHAR(32)     NOT NULL,
                    quantity    DECIMAL(12, 0)  NOT NULL,
                    price       DECIMAL(18, 6)  NOT NULL,
                    book        VARCHAR(32)     NOT NULL,

                    PRIMARY KEY(trade_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trading.unmatched_trade
                (
                    trade_id    INTEGER         NOT NULL,
                    quantity    DECIMAL(12, 0)  NOT NULL,

                    PRIMARY KEY (trade_id, quantity),
                    FOREIGN KEY (trade_id) REFERENCES trading.trade(trade_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trading.matched_trade
                (
                    opening_trade_id    INTEGER NOT NULL,
                    closing_trade_id    INTEGER NOT NULL,

                    PRIMARY KEY(opening_trade_id, closing_trade_id),

                    FOREIGN KEY (opening_trade_id) REFERENCES trading.trade(trade_id),
                    FOREIGN KEY (closing_trade_id) REFERENCES trading.trade(trade_id)
                );
                """
            )

    def drop(self) -> None:
        with self._con.cursor() as cur:
            cur.execute("DROP TABLE trading.matched_trade;")
            cur.execute("DROP TABLE trading.unmatched_trade;")
            cur.execute("DROP TABLE trading.trade;")
            cur.execute("DROP TABLE trading.pnl;")
