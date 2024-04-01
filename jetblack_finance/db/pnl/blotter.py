"""A trade blotter"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from mariadb.connections import Connection
from mariadb.cursors import Cursor

from jetblack_finance.pnl.pnl_implementations import ABCPnl

from ...pnl import FifoPnl
from ...pnl.split_trade import SplitTrade

from .trade import Trade


def _find_instrument(cursor: Cursor, name: str) -> int:
    cursor.execute(
        "SELECT instrument_id FROM trading.instrument WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    assert row is not None, "instrument should exist"
    return row[0]


def _find_book(cursor: Cursor, name: str) -> int:
    cursor.execute(
        "SELECT book_id FROM trading.book WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    assert row is not None, "book should exist"
    return row[0]


def _find_counterparty(cursor: Cursor, name: str) -> int:
    cursor.execute(
        "SELECT counterparty_id FROM trading.counterparty WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    assert row is not None, "counterparty should exist"
    return row[0]


def _find_position(
        cursor: Cursor,
        instrument_id: int,
        book_id: int
) -> Optional[Any]:
    sql = """
SELECT
FROM
    trading.position
WHERE
    instrument_id = ?
AND
    book_id = ?
;"""
    args = (instrument_id, book_id)
    cursor.execute(sql, args)
    row = cursor.fetchone()
    return row


def _insert_trade(
        cursor: Cursor,
        instrument_id: int,
        quantity: Decimal,
        price: Decimal,
        trade_date: date,
        transaction_time: datetime,
        book_id: int,
        counterparty_id: int
) -> Trade:
    sql = """
INSERT INTO trading.trade(
    instrument_id,
    quantity,
    price,
    trade_date,
    transaction_time,
    book_id,
    counterparty_id
) VALUES (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)"""
    args = (
        instrument_id,
        quantity,
        price,
        trade_date,
        transaction_time,
        book_id,
        counterparty_id

    )
    cursor.execute(sql, args)
    return Trade(
        cursor.lastrowid,
        instrument_id,
        quantity,
        price,
        trade_date,
        transaction_time,
        book_id,
        counterparty_id
    )


def _insert_split_trade(
        cursor: Cursor,
        trade: Trade,
        used: Decimal
) -> SplitTrade:
    sql = """
INSERT INTO trading.split_trade(trade_id, used)
VALUES (?, ?)
;"""
    args = (trade.trade_id, used)
    cursor.execute(sql, args)

    return SplitTrade(trade, used)


def insert_position(
        cursor: Cursor,
        split_trade: SplitTrade,
        pnl: ABCPnl,
) -> None:
    sql = """
INSERT INTO trading.position
(
    instrument_id,
    book_id,
    split_trade_id,
    quantity,
    cost,
    realized
) VALUES (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)"""
    args(
        split_trade,
        book_id,
    )


def book_trade(
        conn: Connection,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        trade_date: date,
        transaction_time: datetime,
        book: str,
        counteryparty: str
):
    with conn.cursor() as cur:
        instrument_id = _find_instrument(cur, symbol)
        book_id = _find_book(cur, book)
        counterparty_id = _find_counterparty(cur, counteryparty)

        position_row = _find_position(cur, instrument_id, book_id)

        if position_row is None:
            trade = _insert_trade(
                cur,
                instrument_id,
                quantity,
                price,
                trade_date,
                transaction_time,
                book_id,
                counterparty_id
            )
            pnl: ABCPnl = FifoPnl()
            pnl = pnl + trade
            _insert_position(cursor, pnl)
