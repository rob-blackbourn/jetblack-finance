"""A basic database implementation"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Generic, Optional, TypeVar, cast

import pymysql
import pymysql.cursors
from pymysql import Connection
from pymysql.cursors import Cursor, DictCursor

from jetblack_finance.pnl import (
    IMarketTrade,
    IPnlState,
    IPnlTrade,
    IMatchedPool,
    IUnmatchedPool
)
from jetblack_finance.pnl.pnl_strip import PnlStrip
from jetblack_finance.pnl.algorithm import add_trade

T = TypeVar('T', bound='ABCPnl')


class MarketTrade(IMarketTrade):

    def __init__(
        self, trade_id: int,
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
        # TODO: check that quantity and price are decimals.
        return MarketTrade(trade_id, row['timestamp'], row['ticker'], row['quantity'], row['price'], row['book'])


class PnlTrade(IPnlTrade):

    def __init__(
            self,
            trade: IMarketTrade,
            quantity: Decimal | int
    ) -> None:
        self._trade = trade
        self._quantity = Decimal(quantity)

    @property
    def trade(self) -> IMarketTrade:
        return self._trade

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, PnlTrade) and
            self._trade == value._trade and
            self.quantity == value.quantity
        )

    def __repr__(self) -> str:
        return f"{self.quantity} (of {self._trade.quantity}) @ {self.trade.price}"


class ABCPnl(IPnlState, Generic[T]):

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

    def __init__(
            self,
            cur: Cursor,
            ticker: str,
            book: str,
            quantity: Decimal | int,
            cost: Decimal | int,
            realized: Decimal | int,
            unmatched: IUnmatchedPool,
            matched: IMatchedPool
    ) -> None:
        self._cur = cur
        self._ticker = ticker
        self._book = book
        self._quantity = Decimal(quantity)
        self._cost = Decimal(cost)
        self._realized = Decimal(realized)
        self._unmatched = unmatched
        self._matched = matched

    def add(
        self,
        timestamp: datetime,
        quantity: Decimal,
        price: Decimal,
    ) -> T:
        self._cur.execute(
            """
            INSERT INTO trading.trade(timestamp, ticker, quantity, price, book)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (timestamp.isoformat(), self._ticker, quantity, price, self._book)
        )
        trade_id = self._cur.lastrowid
        trade = MarketTrade(
            trade_id,
            timestamp,
            self._ticker,
            quantity,
            price,
            self._book
        )

        state = add_trade(
            self,
            trade,
            self.create_pnl,
            self.create_partial_trade,
        )
        return cast(T, state)

    @abstractmethod
    def create_pnl(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: IUnmatchedPool,
        matched: IMatchedPool
    ) -> IPnlState:
        ...

    def create_partial_trade(self, trade: IMarketTrade, quantity: Decimal) -> IPnlTrade:
        return PnlTrade(trade, quantity)

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def cost(self) -> Decimal:
        return self._cost

    @property
    def realized(self) -> Decimal:
        return self._realized

    @property
    def unmatched(self) -> IUnmatchedPool:
        return self._unmatched

    @property
    def matched(self) -> IMatchedPool:
        return self._matched

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)
        return -self.cost / self.quantity

    def unrealized(self, price: Decimal) -> Decimal:
        return self.quantity * price + self.cost

    def strip(self, price: Decimal | int) -> PnlStrip:
        return PnlStrip(
            self.quantity,
            self.avg_cost,
            Decimal(price),
            self.realized,
            self.unrealized(Decimal(price))
        )

    def __repr__(self) -> str:
        return f"{self.quantity} @ {self.cost} + {self.realized}"


class FifoPnl(ABCPnl['FifoPnl']):

    class UnmatchedPool(IUnmatchedPool):

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
            pnl_trade = PnlTrade(market_trade, row['quantity'])
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

    @classmethod
    def create(cls, cur: Cursor, ticker: str, book: str) -> FifoPnl:
        cur.execute(
            """
            SELECT
                quantity,
                cost,
                realized
            FROM
                trading.pnl
            WHERE
                ticker = %s
            AND
                book = %s
            """,
            (ticker, book)
        )
        row = cast(dict | None, cur.fetchone())
        quantity, cost, realized = (
            (Decimal(0), Decimal(0), Decimal(0))
            if row is None
            else (row['quantity'], row['cost'], row['realized'])
        )
        return FifoPnl(
            cur,
            ticker,
            book,
            quantity,
            cost,
            realized,
            FifoPnl.UnmatchedPool(cur, ticker, book),
            FifoPnl.MatchedPool(cur, ticker, book)
        )

    def create_pnl(
            self,
            quantity: Decimal,
            cost: Decimal,
            realized: Decimal,
            unmatched: IUnmatchedPool,
            matched: IMatchedPool
    ) -> FifoPnl:
        self._cur.execute(
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
                'ticker': self._ticker,
                'book': self._book,
                'quantity': quantity,
                'cost': cost,
                'realized': realized
            }
        )
        return FifoPnl(
            self._cur,
            self._ticker,
            self._book,
            quantity,
            cost,
            realized,
            unmatched,
            matched
        )


class TradeDb:

    def __init__(self, con: Connection) -> None:
        self._con = con

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


def main():
    con = pymysql.connect(
        host='localhost',
        user='rtb',
        password='thereisnospoon',
        database='trading',
        cursorclass=DictCursor
    )

    trade_db = TradeDb(con)

    trade_db.drop()
    trade_db.create_tables()

    with con.cursor() as cur:
        pnl = FifoPnl.create(cur, 'AAPL', 'tech')

        # Buy 6 @ 100
        ts = datetime(2000, 1, 1, 9, 0, 0, 0)
        pnl = pnl.add(ts, Decimal(6), Decimal(100))
        con.commit()

        # Buy 6 @ 106
        ts += timedelta(seconds=1)
        pnl = pnl.add(ts, Decimal(6), Decimal(106))
        con.commit()

        # Buy 6 @ 103
        ts += timedelta(seconds=1)
        pnl = pnl.add(ts, Decimal(6), Decimal(103))
        con.commit()

        # Sell 9 @ 105
        ts += timedelta(seconds=1)
        pnl = pnl.add(ts, Decimal(-9), Decimal(105))
        con.commit()

        # Sell 9 @ 107
        ts += timedelta(seconds=1)
        pnl = pnl.add(ts, Decimal(-9), Decimal(107))
        con.commit()


if __name__ == '__main__':
    main()
