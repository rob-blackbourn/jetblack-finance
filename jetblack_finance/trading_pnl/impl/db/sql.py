"""SQL statements"""

from pymysql.cursors import Cursor

from ... import TradingPnl


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

            PRIMARY KEY(ticker, book)
        )
        """
    )


def create_table_trade(cur: Cursor) -> None:
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


def create_table_unmatched_trade(cur: Cursor) -> None:
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


def create_table_matched_trade(cur: Cursor) -> None:
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


def save_pnl(cur: Cursor, pnl: TradingPnl, ticker: str, book: str) -> None:
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
