"""An example using a database
"""

from datetime import datetime, timedelta
import os

import pymysql
import pymysql.cursors
from pymysql.constants import CLIENT

from jetblack_finance.trading_pnl.impl.db.mysql import TradeDb


def main():
    con = pymysql.connect(
        host=os.environ['MYSQL_HOSTNAME'],
        user=os.environ['MYSQL_USERNAME'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE'],
        cursorclass=pymysql.cursors.DictCursor,
        client_flag=CLIENT.MULTI_STATEMENTS
    )

    trade_db = TradeDb(con)

    trade_db.drop()
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
