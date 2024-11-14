"""Matched and unmatched pools"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import cast

from pymysql.cursors import Cursor

from ... import (
    PnlTrade,
    IMatchedPool,
    IUnmatchedPool,
)

from .market_trade import MarketTrade
from .sql import MAX_VALID_TO


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
                closing_trade_id,
                valid_from,
                valid_to
            ) VALUES (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                cast(MarketTrade, opening.trade).trade_id,
                cast(MarketTrade, closing.trade).trade_id,
                cast(MarketTrade, closing.trade).timestamp.isoformat(),
                MAX_VALID_TO.isoformat(),
            )
        )


class UnmatchedPool:

    class Fifo(IUnmatchedPool):

        def __init__(self, cur: Cursor, ticker: str, book: str) -> None:
            self._cur = cur
            self._ticker = ticker
            self._book = book

        def push(self, opening: PnlTrade) -> None:
            market_trade = cast(MarketTrade, opening.trade)

            self._cur.execute(
                """
                INSERT INTO trading.unmatched_trade(
                    trade_id,
                    quantity,
                    valid_from,
                    valid_to
                ) VALUES (
                    %(trade_id)s,
                    %(quantity)s,
                    %(valid_from)s,
                    %(valid_to)s
                )
                """,
                {
                    'trade_id': market_trade.trade_id,
                    'quantity': opening.quantity,
                    'valid_from': market_trade.timestamp.isoformat(),
                    'valid_to': MAX_VALID_TO.isoformat()
                }
            )

        def pop(self, closing: PnlTrade) -> PnlTrade:
            # Find the oldest unmatched trade that is in the valid window.
            timestamp = cast(MarketTrade, closing.trade).timestamp
            self._cur.execute(
                """
                SELECT
                    t.timestamp,
                    t.trade_id,
                    ut.quantity,
                    ut.valid_from
                FROM
                    trading.unmatched_trade AS ut
                JOIN
                    trading.trade AS t
                ON
                    t.trade_id = ut.trade_id
                WHERE
                    ut.valid_from <= %(timestamp)s
                AND
                    ut.valid_to = %(max_valid_to)s
                ORDER BY
                    t.timestamp,
                    t.trade_id
                LIMIT
                    1;
                """,
                {
                    'timestamp': timestamp.isoformat(),
                    'max_valid_to': MAX_VALID_TO.isoformat()
                }
            )
            row = cast(dict | None, self._cur.fetchone())
            if row is None:
                raise RuntimeError("no unmatched trades")
            trade_id = cast(int, row['trade_id'])
            quantity = cast(Decimal, row['quantity'])
            valid_from = cast(datetime, row['valid_from'])

            # Remove from unmatched by setting the valid_to to the trade's
            # timestamp
            self._cur.execute(
                """
                update
                    trading.unmatched_trade
                SET
                    valid_to = %(timestamp)s
                WHERE
                    trade_id = %(trade_id)s
                AND
                    quantity = %(quantity)s
                AND
                    valid_from = %(valid_from)s
                AND
                    valid_to = %(max_valid_to)s
                """,
                {
                    'timestamp': timestamp.isoformat(),
                    'trade_id': trade_id,
                    'quantity': quantity,
                    'valid_from': valid_from.isoformat(),
                    'max_valid_to': MAX_VALID_TO.isoformat()
                }
            )
            market_trade = MarketTrade.read(self._cur, trade_id)
            if market_trade is None:
                raise RuntimeError("unable to find market trade")
            pnl_trade = PnlTrade(quantity, market_trade)
            return pnl_trade

        def has(self, closing: PnlTrade) -> bool:
            timestamp = cast(MarketTrade, closing.trade).timestamp
            self._cur.execute(
                """
                SELECT
                    COUNT(ut.trade_id) AS count
                FROM
                    trading.unmatched_trade AS ut
                JOIN
                    trading.trade AS t
                ON
                    t.trade_id = ut.trade_id
                AND
                    t.ticker = %(ticker)s
                AND
                    t.book = %(book)s
                WHERE
                    ut.valid_from <= %(timestamp)s AND %(timestamp)s < ut.valid_to
                """,
                {
                    'ticker': self._ticker,
                    'book': self._book,
                    'timestamp': timestamp.isoformat()
                }
            )
            row = cast(dict | None, self._cur.fetchone())
            assert (row is not None)
            return row['count'] != 0
