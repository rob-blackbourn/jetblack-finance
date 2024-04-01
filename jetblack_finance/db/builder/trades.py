"""Trades"""

from mariadb.connections import Connection


def _create_table(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
CREATE TABLE trade
(
    trade_id            INT             NOT NULL    AUTO_INCREMENT,
    instrument_id       INT             NOT NULL,
    quantity            NUMERIC(18, 2)  NOT NULL,
    price               NUMERIC(18, 5)  NOT NULL,
    trade_date          DATE            NOT NULL,
    transaction_time    DATETIME        NOT NULL,
    book_id             INT             NOT NULL,
    counterparty_id     INT             NOT NULL,

    PRIMARY KEY (trade_id),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    FOREIGN KEY (counterparty_id) REFERENCES counterparty(counterparty_id)
) WITH SYSTEM VERSIONING;
""")
        conn.commit()


def create_trades(conn: Connection) -> None:
    print("Creating the trades")
    _create_table(conn)
