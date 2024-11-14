"""SQLite example"""

from decimal import Decimal
import sqlite3


def adapt_decimal(value: Decimal) -> str:
    text = str(value)
    return text


def convert_decimal(buf: bytes) -> Decimal:
    text = buf.decode('ascii')
    value = Decimal(text)
    return value


def main():
    # Register the adapter
    sqlite3.register_adapter(Decimal, adapt_decimal)

    # Register the converter
    sqlite3.register_converter("decimal", convert_decimal)

    d = Decimal('4.12')

    con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
    cur = con.cursor()
    cur.execute("create table test(d decimal)")

    cur.execute("insert into test(d) values (?)", (d,))
    cur.execute("select d from test")
    data = cur.fetchone()[0]
    print(data)
    print(type(data))

    cur.close()
    con.close()


if __name__ == '__main__':
    main()
