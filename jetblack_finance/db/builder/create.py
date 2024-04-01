"""Load"""

import os

import mariadb
from mariadb.connections import Connection

from .books import create_books
from .counterparties import create_counterparties
from .currencies import create_currencies
from .instruments import create_instruments
from .positions import create_positions
from .schema import create_schema, drop_schema
from .trades import create_trades


def _create_schema(host: str, port: int, user: str, password: str, schema_name: str):
    print("Creating the schema")
    # Create the schema from the mysql database.
    conn = mariadb.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        db='sys'
    )
    drop_schema(conn, schema_name)
    create_schema(conn, schema_name)


def _create_tables(conn: Connection) -> None:
    """Create the tables"""

    create_currencies(conn)
    create_instruments(conn)
    create_books(conn)
    create_counterparties(conn)
    create_trades(conn)
    create_positions(conn)


def main(host: str, port: int, user: str, password: str, schema_name: str):
    """Create the database"""

    # Create the schema
    _create_schema(host, port, user, password, schema_name)

    conn = mariadb.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        db=schema_name
    )

    _create_tables(conn)

    conn.close()


def start():
    HOST = 'localhost'
    PORT = 3306
    USER = 'admin'
    PASSWORD = os.environ['DB_PASSWORD']
    SCHEMA_NAME = 'trading'
    main(HOST, PORT, USER, PASSWORD, SCHEMA_NAME)


if __name__ == '__main__':
    start()
