"""SQL statements"""

from datetime import datetime
from decimal import Decimal
from typing import cast

from pymysql.cursors import Cursor

from .... import TradingPnl

MAX_VALID_TO = datetime(9999, 12, 31, 23, 59, 59)


def create_table_pnl(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trading.pnl
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
        CREATE TABLE IF NOT EXISTS trading.trade
        (
            trade_id    INTEGER         NOT NULL AUTO_INCREMENT,
            timestamp   DATETIME        NOT NULL,
            ticker      VARCHAR(32)     NOT NULL,
            quantity    DECIMAL(12, 0)  NOT NULL,
            price       DECIMAL(18, 6)  NOT NULL,
            book        VARCHAR(32)     NOT NULL,

            PRIMARY KEY(trade_id)
        );
        """
    )


def create_table_unmatched_trade(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trading.unmatched_trade
        (
            trade_id    INTEGER         NOT NULL,
            quantity    DECIMAL(12, 0)  NOT NULL,

            valid_from  DATETIME        NOT NULL,
            valid_to    DATETIME        NOT NULL,

            PRIMARY KEY (valid_from, valid_to, trade_id, quantity),
            FOREIGN KEY (trade_id) REFERENCES trading.trade(trade_id)
        );
        """
    )


def create_table_matched_trade(cur: Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trading.matched_trade
        (
            opening_trade_id        INTEGER NOT NULL,
            closing_trade_id        INTEGER NOT NULL,

            valid_from  DATETIME    NOT NULL,
            valid_to    DATETIME    NOT NULL,

            PRIMARY KEY(valid_from, valid_to, opening_trade_id, closing_trade_id),

            FOREIGN KEY (opening_trade_id) REFERENCES trading.trade(trade_id),
            FOREIGN KEY (closing_trade_id) REFERENCES trading.trade(trade_id)
        );
        """
    )


def create_tables(cur: Cursor) -> None:
    create_table_pnl(cur)
    create_table_trade(cur)
    create_table_unmatched_trade(cur)
    create_table_matched_trade(cur)


def drop_tables(cur: Cursor) -> None:
    cur.execute("DROP TABLE trading.matched_trade;")
    cur.execute("DROP TABLE trading.unmatched_trade;")
    cur.execute("DROP TABLE trading.trade;")
    cur.execute("DROP TABLE trading.pnl;")


def ensure_pnl(cur: Cursor, ticker: str, book: str, timestamp: datetime) -> None:
    # There should be no pnl on or after this timestamp.
    cur.execute(
        """
        SELECT
            COUNT(*) AS count
        FROM
            trading.pnl
        WHERE
            ticker = %(ticker)s
        AND
            book = %(book)s
        AND
            valid_from >= %(timestamp)s;
        """,
        {
            'ticker': ticker,
            'book': book,
            'timestamp': timestamp.isoformat(),
        }
    )
    row = cast(dict | None, cur.fetchone())
    assert (row is not None)
    if row['count'] != 0:
        raise RuntimeError("there is already p/l for this timestamp")


def select_pnl(cur: Cursor, ticker: str, book: str, timestamp: datetime) -> TradingPnl:
    cur.execute(
        """
        SELECT
            quantity,
            cost,
            realized
        FROM
            trading.pnl
        WHERE
            ticker = %(ticker)s
        AND
            book = %(book)s
        AND
            valid_from <= %(timestamp)s
        AND
            valid_to = %(max_valid_to)s
        """,
        {
            'ticker': ticker,
            'book': book,
            'timestamp': timestamp.isoformat(),
            'max_valid_to': MAX_VALID_TO.isoformat()
        }
    )
    row = cast(dict | None, cur.fetchone())
    if row is None:
        return TradingPnl(Decimal(0), Decimal(0), Decimal(0))

    return TradingPnl(row['quantity'], row['cost'], row['realized'])


def save_pnl(cur: Cursor, pnl: TradingPnl, ticker: str, book: str, timestamp: datetime) -> None:
    cur.execute(
        """
        UPDATE
            trading.pnl
        SET
            valid_to = %(timestamp)s
        WHERE
            ticker = %(ticker)s
        AND
            book = %(book)s
        AND
            valid_from <= %(timestamp)s
        AND
            valid_to = %(max_valid_to)s;

        INSERT INTO trading.pnl
        (
            ticker,
            book,
            quantity,
            cost,
            realized,
            valid_from,
            valid_to
        ) VALUES (
            %(ticker)s,
            %(book)s,
            %(quantity)s,
            %(cost)s,
            %(realized)s,
            %(timestamp)s,
            %(max_valid_to)s
        ) ON DUPLICATE KEY UPDATE
            quantity = %(quantity)s,
            cost = %(cost)s,
            realized = %(realized)s;
        """,
        {
            'ticker': ticker,
            'book': book,
            'quantity': pnl.quantity,
            'cost': pnl.cost,
            'realized': pnl.realized,
            'timestamp': timestamp.isoformat(),
            'max_valid_to': MAX_VALID_TO.isoformat()
        }
    )
