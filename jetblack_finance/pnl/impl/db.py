"""A basic database implementation"""

from datetime import datetime
from decimal import Decimal
import duckdb


def create_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
CREATE SEQUENCE table_id START 1;

CREATE TABLE trade
(
    trade_id            INTEGER         NOT NULL DEFAULT nextval('table_id'),
    timestamp           TIMESTAMP       NOT NULL,
    ticker              VARCHAR(32)     NOT NULL,
    quantity            DECIMAL(12, 0)  NOT NULL,
    price               DECIMAL(18, 6)  NOT NULL,
    book                VARCHAR(32)     NOT NULL,

    PRIMARY KEY(trade_id)
);

CREATE TABLE partial_trade
(
    
)
        """
    )


def insert_trade(
        con: duckdb.DuckDBPyConnection,
        timestamp: datetime,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        book: str
) -> int:
    con.execute(
        """
INSERT INTO trade(timestamp, ticker, quantity, price, book)
VALUES (?, ?, ?, ?, ?)
""",
        (timestamp, ticker, quantity, price, book)
    )
    results = con.fetchone()
    assert results is not None
    return results[0]


def main():
    con = duckdb.connect(":memory:")

    create_tables(con)
    trade_id = insert_trade(
        con,
        datetime(2024, 1, 5, 9, 0, 0),
        'AAPL',
        Decimal(1),
        Decimal(213.25),
        'TECH_STOCKS'
    )
    print(trade_id)


if __name__ == '__main__':
    main()
