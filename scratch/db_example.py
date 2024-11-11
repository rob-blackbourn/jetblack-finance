"""An example using a database
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pymysql
import pymysql.cursors

from jetblack_finance.trading_pnl.impl.db import TradeDb


def main():
    con = pymysql.connect(
        host='localhost',
        user='rtb',
        password='thereisnospoon',
        database='trading',
        cursorclass=pymysql.cursors.DictCursor
    )

    trade_db = TradeDb(con)

    trade_db.drop()
    trade_db.create_tables()

    ticker = 'AAPL'
    book = 'tech'

    # Buy 6 @ 100
    ts = datetime(2000, 1, 1, 9, 0, 0, 0)
    pnl = trade_db.add_trade(ts, ticker, Decimal(6), Decimal(100), book)
    print(pnl)

    # Buy 6 @ 106
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, Decimal(6), Decimal(106), book)
    print(pnl)

    # Buy 6 @ 103
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, Decimal(6), Decimal(103), book)
    print(pnl)

    # Sell 9 @ 105
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, Decimal(-9), Decimal(105), book)
    print(pnl)

    # Sell 9 @ 107
    ts += timedelta(seconds=1)
    pnl = trade_db.add_trade(ts, ticker, Decimal(-9), Decimal(107), book)
    print(pnl)


if __name__ == '__main__':
    main()
