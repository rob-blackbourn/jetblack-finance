"""Positions"""

from mariadb.connections import Connection


def _create_table(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
CREATE TABLE split_trade
(
    split_trade_id          INT             NOT NULL    AUTO_INCREMENT,
    trade_id                INT             NOT NULL,
    used                    NUMERIC(18, 2)  NOT NULL,
    
    PRIMARY KEY (split_trade_id),
    FOREIGN KEY (trade_id) REFERENCES trade(trade_id)
) WITH SYSTEM VERSIONING;
""")

        cur.execute("""
CREATE TABLE unmatched
(
    unmatched_id            INT             NOT NULL    AUTO_INCREMENT,
    split_trade_id          INT             NOT NULL,

    PRIMARY KEY (unmatched_id),
    UNIQUE (split_trade_id),
    FOREIGN KEY (split_trade_id) REFERENCES split_trade(split_trade_id)
) WITH SYSTEM VERSIONING;
""")

        cur.execute("""
CREATE TABLE matched
(
    matched_id              INT             NOT NULL    AUTO_INCREMENT,
    open_split_trade_id     INT             NOT NULL,
    close_split_trade_id    INT             NOT NULL,

    PRIMARY KEY (matched_id),
    UNIQUE (open_split_trade_id, close_split_trade_id),
    FOREIGN KEY (open_split_trade_id) REFERENCES split_trade(split_trade_id),
    FOREIGN KEY (close_split_trade_id) REFERENCES split_trade(split_trade_id)
) WITH SYSTEM VERSIONING;
""")

        cur.execute("""
CREATE TABLE position
(
    position_id             INT             NOT NULL    AUTO_INCREMENT,
    instrument_id           INT             NOT NULL,
    book_id                 INT             NOT NULL,
    last_trade_id           INT             NOT NULL,
    quantity                NUMERIC(18, 2)  NOT NULL,
    cost                    NUMERIC(18, 2)  NOT NULL,
    realized                NUMERIC(18, 2)  NOT NULL,
    
    PRIMARY KEY (position_id),
    UNIQUE (instrument_id, book_id),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    FOREIGN KEY (last_trade_id) REFERENCES trade(trade_id)
) WITH SYSTEM VERSIONING;
""")

        conn.commit()


def create_positions(conn: Connection) -> None:
    print("Creating the positions")
    _create_table(conn)
