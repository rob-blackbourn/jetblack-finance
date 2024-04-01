"""A database trade"""

from datetime import date, datetime
from decimal import Decimal

from ...pnl import ITrade


class Trade(ITrade):

    def __init__(
            self,
            trade_id: int,
            instrument_id: int,
            quantity: Decimal,
            price: Decimal,
            trade_date: date,
            transaction_time: datetime,
            book_id: int,
            countryparty_id: int
    ) -> None:
        self._trade_id = trade_id
        self._instrument_id = instrument_id
        self._quantity = quantity
        self._price = price
        self._trade_date = trade_date
        self._transaction_time = transaction_time
        self._book_id = book_id
        self._counterparty_id = countryparty_id

    @property
    def trade_id(self) -> int:
        return self._trade_id

    @property
    def instrument_id(self) -> int:
        return self._instrument_id

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def trade_date(self) -> date:
        return self._trade_date

    @property
    def transaction_time(self) -> datetime:
        return self._transaction_time

    @property
    def book_id(self) -> int:
        return self._book_id

    @property
    def counterparty_id(self) -> int:
        return self._counterparty_id
