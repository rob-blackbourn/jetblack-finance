"""Matched and unmatched pools"""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from pymysql.cursors import Cursor

from ... import (
    PnlTrade,
    IMatchedPool,
    IUnmatchedPool,
)

from .market_trade import MarketTrade


class MatchedPool(IMatchedPool):

    def __init__(self, cur: Cursor, ticker: str, book: str) -> None:
        self._cur = cur
        self._ticker = ticker
        self._book = book

    def push(self, opening: PnlTrade, closing: PnlTrade) -> None:
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

        def push(self, pnl_trade: PnlTrade) -> None:
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

        def pop(self, _quantity: Decimal, _cost: Decimal) -> PnlTrade:
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
            pnl_trade = PnlTrade(row['quantity'], market_trade)
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
