"""Create the database with SQLAlchemy"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Tuple
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship
)


class Base(DeclarativeBase):
    pass


class Currency(Base):
    __tablename__ = "currency"

    currency_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(200), unique=True)
    ccy: Mapped[str] = mapped_column(String(3), unique=True)
    minor_unit: Mapped[int]
    numeric_code: Mapped[int] = mapped_column(unique=True)


class Instrument(Base):
    __tablename__ = "instrument"

    instrument_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(200), unique=True)
    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currency.currency_id")
    )
    ccy: Mapped[Currency] = relationship()


class Book(Base):
    __tablename__ = "book"

    book_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(200), unique=True)


class Counterparty(Base):
    __tablename__ = "counterparty"

    counterparty_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(200), unique=True)


class Trade(Base):
    __tablename__ = "trade"

    trade_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instrument.instrument_id")
    )
    instrument: Mapped[Instrument] = relationship()

    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 5))
    trade_date: Mapped[date] = mapped_column(Date)
    transaction_time: Mapped[datetime] = mapped_column(DateTime)

    currency_id: Mapped[int] = mapped_column(
        ForeignKey("currency.currency_id")
    )
    ccy: Mapped[Currency] = relationship()

    book_id: Mapped[int] = mapped_column(
        ForeignKey("book.book_id")
    )
    book: Mapped[Book] = relationship()

    counterparty_id: Mapped[int] = mapped_column(
        ForeignKey("counterparty.counterparty_id")
    )
    counterparty: Mapped[Counterparty] = relationship()


class SplitTrade(Base):
    __tablename__ = "split_trade"

    split_trade_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trade.trade_id")
    )
    trade: Mapped[Trade] = relationship()
    used: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal(0))

    @property
    def quantity(self) -> Decimal:
        return self.trade.quantity - self.used

    @property
    def price(self) -> Decimal:
        return self.trade.price

    def split(self, quantity: Decimal) -> Tuple[SplitTrade, SplitTrade]:
        assert abs(self.quantity) >= abs(quantity)
        unused = self.quantity - quantity
        matched = SplitTrade(
            trade=self.trade,
            used=self.used + unused
        )
        unmatched = SplitTrade(
            trade=self.trade,
            used=self.used + quantity
        )
        return matched, unmatched


class UnmatchedTrade(Base):
    __tablename__ = "unmatched_trade"

    unmatched_trade_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    split_trade_id: Mapped[int] = mapped_column(
        ForeignKey("split_trade.split_trade_id"),
        unique=True
    )
    split_trade: Mapped[SplitTrade] = relationship()


class MatchedTrade(Base):
    __tablename__ = "matched_trade"

    matched_trade_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    open_split_trade_id: Mapped[int] = mapped_column(
        ForeignKey("split_trade.split_trade_id"),
        unique=True
    )
    open_split_trade: Mapped[SplitTrade] = relationship(
        foreign_keys=[open_split_trade_id]
    )

    close_split_trade_id: Mapped[int] = mapped_column(
        ForeignKey("split_trade.split_trade_id"),
        unique=True
    )
    close_split_trade: Mapped[SplitTrade] = relationship(
        foreign_keys=[close_split_trade_id]
    )


class Position(Base):
    __tablename__ = "position"

    position_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    instrument_id: Mapped[int] = mapped_column(
        ForeignKey("instrument.instrument_id")
    )
    instrument: Mapped[Instrument] = relationship()

    book_id: Mapped[int] = mapped_column(
        ForeignKey("book.book_id")
    )
    book: Mapped[Book] = relationship()

    split_trade_id: Mapped[int] = mapped_column(
        ForeignKey("split_trade.split_trade_id"),
        unique=True
    )
    split_trade: Mapped[SplitTrade] = relationship()

    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 5))
    realized: Mapped[Decimal] = mapped_column(Numeric(18, 5))

    __table_args__ = (
        UniqueConstraint(
            'instrument_id',
            'book_id',
            'split_trade_id',
            # name='_customer_location_uc'
        ),
    )


def main():
    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        usd = Currency(
            ccy='USD',
            name='US Dollar',
            minor_unit=2,
            numeric_code=840
        )
        ibm = Instrument(name='IBM Inc', ccy=usd)
        tech_stocks = Book(name='tech stocks')
        fatbank = Counterparty(name='FatBank')
        session.add_all([usd, ibm, tech_stocks, fatbank])
        session.commit()

        t1 = Trade(
            instrument=ibm,
            quantity=Decimal(100),
            price=Decimal(189.14),
            trade_date=date(2024, 4, 7),
            transaction_time=datetime(2024, 4, 7, 10, 17),
            ccy=usd,
            book=tech_stocks,
            counterparty=fatbank
        )
        session.add_all([t1])
        session.commit()

        print("Here")


if __name__ == '__main__':
    main()
