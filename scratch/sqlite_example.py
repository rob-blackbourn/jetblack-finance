"""SQLite example"""

from datetime import datetime
from decimal import Decimal
import sqlite3
from typing import Callable, Generic, TypeVar, ContextManager

T = TypeVar('T')


class context(ContextManager, Generic[T]):
    def __init__(self, value: T, on_exit: Callable[[T], None]):
        self._value = value
        self._on_exit = on_exit

    def __enter__(self) -> T:
        return self._value

    def __exit__(self, exc_type, exc_value, traceback):
        self._on_exit(self._value)


def adapt_decimal(value: Decimal) -> str:
    text = str(value)
    return text


def convert_decimal(buf: bytes) -> Decimal:
    text = buf.decode('ascii')
    value = Decimal(text)
    return value


def adapt_datetime(val: datetime) -> str:
    return val.isoformat()


def convert_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode())


def register_handlers() -> None:
    # Add decimal support
    sqlite3.register_adapter(Decimal, adapt_decimal)
    sqlite3.register_converter("DECIMAL", convert_decimal)

    # Add datetime support
    sqlite3.register_adapter(datetime, adapt_datetime)
    sqlite3.register_converter("DATETIME", convert_datetime)


def main():
    register_handlers()

    with context(
        sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES),
        lambda con: con.close()
    ) as con:
        with context(con.cursor(), lambda cur: cur.close()) as cur:
            cur.execute(
                """
                CREATE TABLE test
                (
                    num DECIMAL,
                    timestamp DATETIME
                )
                """
            )

            cur.execute(
                """
                INSERT INTO test(num, timestamp)
                VALUES (?, ?)
                """,
                (Decimal('4.12'), datetime(2022, 12, 31, 15, 12, 45))
            )
            cur.execute(
                """
                SELECT
                    num,
                    timestamp
                FROM
                    test
                """
            )
            for v in cur.fetchone():
                print(v)
                print(type(v))


if __name__ == '__main__':
    main()
