"""A basic database implementation"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, cast

from pymysql import Connection
from pymysql.cursors import Cursor

from .. import (
    IMarketTrade,
    TradingPnl,
    IPnlTrade,
    IMatchedPool,
    IUnmatchedPool,
    add_trade
)


class MarketTrade(IMarketTrade):

    def __init__(
        self,
        trade_id: int,
        timestamp: datetime,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        book: str
    ) -> None:
        self._trade_id = trade_id
        self._timestamp = timestamp
        self._ticker = ticker
        self._quantity = quantity
        self._price = price
        self._book = book

    @property
    def trade_id(self) -> int:
        return self._trade_id

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def ticker(self) -> str:
        return self._ticker

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def book(self) -> str:
        return self._book

    def __repr__(self) -> str:
        return f"[{self.trade_id}: {self.timestamp.isoformat()}] {self.quantity} {self.ticker} @ {self.price} in {self.book}"

    @classmethod
    def read(cls, cur: Cursor, trade_id: int) -> Optional[MarketTrade]:
        cur.execute(
            """
            SELECT
                timestamp,
                ticker,
                quantity,
                price,
                book
            FROM
                trading.trade
            WHERE
                trade_id = %s
            """,
            (trade_id,)
        )
        row = cast(dict | None, cur.fetchone())
        if row is None:
            return None
        return MarketTrade(trade_id, row['timestamp'], row['ticker'], row['quantity'], row['price'], row['book'])

    @classmethod
    def create(
        cls,
        cur: Cursor,
        timestamp: datetime,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        book: str
    ) -> MarketTrade:
        cur.execute(
            """
            INSERT INTO trading.trade(timestamp, ticker, quantity, price, book)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (timestamp.isoformat(), ticker, quantity, price, book)
        )
        trade_id = cur.lastrowid
        trade = MarketTrade(
            trade_id,
            timestamp,
            ticker,
            quantity,
            price,
            book
        )
        return trade


class MatchedPool(IMatchedPool):

    def __init__(self, cur: Cursor, ticker: str, book: str) -> None:
        self._cur = cur
        self._ticker = ticker
        self._book = book

    def push(self, opening: IPnlTrade, closing: IPnlTrade) -> None:
        self._cur.execute(
            """
            INSERT INTO trading.matched_trade(
                opening_trade_id,
                closing_trade_id
            ) VALUES (
                %s,
                %s
            )
            """,
            (
                cast(MarketTrade, opening.trade).trade_id,
                cast(MarketTrade, closing.trade).trade_id
            )
        )

    def __len__(self) -> int:
        self._cur.execute(
            """
            SELECT
                COUNT(mt.*) AS count
            FROM
                trading.matched_trade AS mt
            JOIN
                trading.trade AS t
            ON
                t.trading_id = mt.opening_trade_id
            AND
                t.ticker = %(ticker)s
            AND
                t.book = %(book)s
            """,
            {
                'ticker': self._ticker,
                'book': self._book
            }
        )
        row = cast(dict | None, self._cur.fetchone())
        return 0 if row is None else row['count']


class UnmatchedPool:

    class Fifo(IUnmatchedPool):
        def __init__(self, cur: Cursor, ticker: str, book: str) -> None:
            self._cur = cur
            self._ticker = ticker
            self._book = book

        def push(self, pnl_trade: IPnlTrade) -> None:
            self._cur.execute(
                """
                INSERT INTO trading.unmatched_trade(
                    trade_id,
                    quantity
                ) VALUES (
                    %s,
                    %s
                )
                """,
                (
                    cast(MarketTrade, pnl_trade.trade).trade_id,
                    pnl_trade.quantity
                )
            )

        def pop(self, _quantity: Decimal, _cost: Decimal) -> IPnlTrade:
            # Find the oldest unmatched trade.
            self._cur.execute(
                """
                SELECT
                    t.timestamp,
                    t.trade_id,
                    ut.quantity
                FROM
                    trading.unmatched_trade AS ut
                JOIN
                    trading.trade AS t
                ON
                    t.trade_id = ut.trade_id
                ORDER BY
                    t.timestamp,
                    t.trade_id
                LIMIT
                    1
                """
            )
            row = cast(dict | None, self._cur.fetchone())
            if row is None:
                raise RuntimeError("no unmatched trades")

            # Remove from unmatched
            self._cur.execute(
                """
                DELETE FROM
                    trading.unmatched_trade
                WHERE
                    trade_id = %(trade_id)s
                AND
                    quantity = %(quantity)s
                """,
                row
            )
            market_trade = MarketTrade.read(self._cur, row['trade_id'])
            if market_trade is None:
                raise RuntimeError("unable to find market trade")
            pnl_trade = IPnlTrade(row['quantity'], market_trade)
            return pnl_trade

        def __len__(self) -> int:
            self._cur.execute(
                """
                SELECT
                    COUNT(ut.*) AS count
                FROM
                    trading.unmatched_trade AS ut
                JOIN
                    trading.trade AS t
                ON
                    t.trading_id = ut.trade_id
                AND
                    t.ticker = %(ticker)s
                AND
                    book = %(book)s
                """,
                {
                    'ticker': self._ticker,
                    'book': self._book
                }
            )
            row = cast(dict | None, self._cur.fetchone())
            return 0 if row is None else row['count']


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
