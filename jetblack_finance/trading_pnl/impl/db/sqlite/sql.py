"""SQL statements"""

from datetime import datetime
from decimal import Decimal

from sqlite3 import Cursor

from .... import TradingPnl

MAX_VALID_TO = datetime(9999, 12, 31, 23, 59, 59)


def create_table_pnl(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pnl
        (
            ticker      VARCHAR(32)     NOT NULL,
            book        VARCHAR(32)     NOT NULL,
            quantity    DECIMAL(12, 0)  NOT NULL,
            cost        DECIMAL(18, 6)  NOT NULL,
            realized    DECIMAL(18, 6)  NOT NULL,

            valid_from  DATETIME        NOT NULL,
            valid_to    DATETIME        NOT NULL,

            PRIMARY KEY(valid_from, valid_to, ticker, book)
        )
        """
    )


def create_table_trade(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trade
        (
            trade_id    INTEGER         NOT NULL,
            timestamp   DATETIME        NOT NULL,
            ticker      TEXT            NOT NULL,
            quantity    DECIMAL         NOT NULL,
            price       DECIMAL         NOT NULL,
            book        TEXT            NOT NULL,

            PRIMARY KEY(trade_id)
        );
        """
    )


def create_table_unmatched_trade(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS unmatched_trade
        (
            trade_id    INTEGER         NOT NULL,
            quantity    DECIMAL         NOT NULL,

            valid_from  DATETIME        NOT NULL,
            valid_to    DATETIME        NOT NULL,

            PRIMARY KEY (valid_from, valid_to, trade_id, quantity),
            FOREIGN KEY (trade_id) REFERENCES trade(trade_id)
        );
        """
    )


def create_table_matched_trade(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matched_trade
        (
            opening_trade_id    INTEGER     NOT NULL,
            closing_trade_id    INTEGER     NOT NULL,

            valid_from          DATETIME    NOT NULL,
            valid_to            DATETIME    NOT NULL,

            PRIMARY KEY(valid_from, valid_to, opening_trade_id, closing_trade_id),

            FOREIGN KEY (opening_trade_id) REFERENCES trade(trade_id),
            FOREIGN KEY (closing_trade_id) REFERENCES trade(trade_id)
        );
        """
    )


def create_tables(cur: Cursor) -> None:
    create_table_pnl(cur)
    create_table_trade(cur)
    create_table_unmatched_trade(cur)
    create_table_matched_trade(cur)


def drop_tables(cur: Cursor) -> None:
    cur.execute("DROP TABLE matched_trade;")
    cur.execute("DROP TABLE unmatched_trade;")
    cur.execute("DROP TABLE trade;")
    cur.execute("DROP TABLE pnl;")


def ensure_pnl(cur: Cursor, ticker: str, book: str, timestamp: datetime) -> None:
    # There should be no pnl on or after this timestamp.
    cur.execute(
        """
        SELECT
            COUNT(*) AS count
        FROM
            pnl
        WHERE
            ticker = ?
        AND
            book = ?
        AND
            valid_from >= ?;
        """,
        (ticker, book, timestamp)
    )
    row = cur.fetchone()
    assert (row is not None)
    (count,) = row
    if count != 0:
        raise RuntimeError("there is already p/l for this timestamp")


def select_pnl(cur: Cursor, ticker: str, book: str, timestamp: datetime) -> TradingPnl:
    cur.execute(
        """
        SELECT
            quantity,
            cost,
            realized
        FROM
            pnl
        WHERE
            ticker = ?
        AND
            book = ?
        AND
            valid_from <= ?
        AND
            valid_to = ?
        """,
        (ticker, book, timestamp, MAX_VALID_TO)
    )
    row = cur.fetchone()
    if row is None:
        return TradingPnl(Decimal(0), Decimal(0), Decimal(0))
    (quantity, cost, realized) = row

    return TradingPnl(quantity, cost, realized)


def save_pnl(cur: Cursor, pnl: TradingPnl, ticker: str, book: str, timestamp: datetime) -> None:
    cur.execute(
        """
        UPDATE
            pnl
        SET
            valid_to = ?
        WHERE
            ticker = ?
        AND
            book = ?
        AND
            valid_from <= ?
        AND
            valid_to = ?;
        """,
        (timestamp, ticker, book, timestamp, MAX_VALID_TO)
    )

    cur.execute(
        """
        INSERT INTO pnl
        (
            ticker,
            book,
            quantity,
            cost,
            realized,
            valid_from,
            valid_to
        ) VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        );
        """,
        (
            ticker,
            book,
            pnl.quantity,
            pnl.cost,
            pnl.realized,
            timestamp,
            MAX_VALID_TO
        )
    )
