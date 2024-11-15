"""SQLite example"""

from datetime import datetime, timedelta
from decimal import Decimal
import sqlite3

from jetblack_finance.trading_pnl.impl.db.sqlite import TradeDb


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
    con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    trade_db = TradeDb(con)

    # trade_db.drop()
    trade_db.create_tables()

    ticker = 'AAPL'
    book = 'tech'

    # Buy 6 @ 100
    ts = datetime(2000, 1, 1, 9, 0, 0, 0)
    pnl = trade_db.add_trade(ts, ticker, 6, 100, book)
    print(pnl)

    # Buy 6 @ 106
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, 6, 106, book)
    print(pnl)

    # Buy 6 @ 103
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, 6, 103, book)
    print(pnl)

    # Sell 9 @ 105
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, -9, 105, book)
    print(pnl)

    # Sell 9 @ 107
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, -9, 107, book)
    print(pnl)

    con.close()


if __name__ == '__main__':
    main()
