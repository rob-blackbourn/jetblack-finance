"""Currencies"""

from mariadb.connections import Connection

from .instrument_types import create_instrument_types
from .cash import create_cash
from .equities import create_equities


def _create_table(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
CREATE TABLE instrument
(
    instrument_id           INT             NOT NULL    AUTO_INCREMENT,
    instrument_type_id      INT             NOT NULL,
    name                    VARCHAR(256)    NOT NULL,

    PRIMARY KEY (instrument_id),
    UNIQUE (name),
    FOREIGN KEY (instrument_type_id) REFERENCES instrument_type(instrument_type_id)
) WITH SYSTEM VERSIONING;
""")
        conn.commit()


def create_instruments(conn: Connection) -> None:
    create_instrument_types(conn)

    print("Creating the instruments")
    _create_table(conn)

    create_cash(conn)
    create_equities(conn)
