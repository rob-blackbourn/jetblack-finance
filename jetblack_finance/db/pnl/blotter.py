"""A trade blotter"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional, Sequence, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from jetblack_finance.pnl import ITrade, ISplitTrade
from jetblack_finance.pnl.algorithm import add_split_trade
from jetblack_finance.pnl.pnl_state import IPnlState
from jetblack_finance.pnl.pnl_implementations import ABCPnl


from jetblack_finance.db.builder.create_sqlalchemy import (
    Base,
    Currency,
    Instrument,
    Book,
    Counterparty,
    Trade,
    SplitTrade,
    MatchedTrade,
    UnmatchedTrade,
    Position
)


class FifoPnl(ABCPnl):

    def __init__(
        self,
        session: Session,
        instrument: Instrument,
        book: Book,
        pnl_state: Optional[IPnlState] = None
    ) -> None:
        super().__init__(pnl_state)
        self._session = session
        self._instrument = instrument
        self._book = book

    def __add__(self, trade: Any) -> FifoPnl:
        assert isinstance(trade, Trade)
        split_trade = SplitTrade(trade=trade)
        state = add_split_trade(
            self._pnl_state,
            split_trade,
            self.create_pnl,
            self.push_unmatched,
            self.pop_unmatched,
            self.push_matched
        )
        return FifoPnl(
            self._session,
            self._instrument,
            self._book,
            state
        )

    def create(
        self,
        pnl_state: IPnlState
    ) -> ABCPnl:
        return FifoPnl(
            self._session,
            self._instrument,
            self._book,
            pnl_state
        )

    def split_trade(self, trade: ITrade) -> ISplitTrade:
        return SplitTrade(trade=trade)

    def create_pnl(
        self,
        quantity: Decimal,
        cost: Decimal,
        realized: Decimal,
        unmatched: Sequence[ISplitTrade],
        matched: Sequence[Tuple[ISplitTrade, ISplitTrade]]
    ) -> IPnlState:
        _opening, closing = matched[0]
        self._session.add(
            Position(
                instrument=self._instrument,
                book=self._book,
                split_trade=closing,
                quantity=quantity,
                cost=cost,
                realized=realized
            )
        )
        return self.create_pnl(
            quantity,
            cost,
            realized,
            unmatched,
            matched
        )

    def pop_unmatched(
            self,
            unmatched: Sequence[ISplitTrade]
    ) -> Tuple[ISplitTrade, Sequence[ISplitTrade]]:
        self._session.delete(unmatched[0])
        return unmatched[0], unmatched[1:]

    def push_unmatched(
            self,
            split_trade: ISplitTrade,
            unmatched: Sequence[ISplitTrade]
    ) -> Sequence[ISplitTrade]:
        self._session.add(UnmatchedTrade(split_trade=split_trade))
        return [split_trade] + list(unmatched)

    def push_matched(
            self,
            opening: ISplitTrade, closing: ISplitTrade,
            matched: Sequence[Tuple[ISplitTrade, ISplitTrade]]
    ) -> Sequence[Tuple[ISplitTrade, ISplitTrade]]:
        self._session.add(MatchedTrade(opening=opening, closing=closing))
        return list(matched) + [(opening, closing)]


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
        session.add(t1)

        pnl = FifoPnl(
            session,
            ibm,
            fatbank
        )

        pnl2 = pnl + t1
        session.commit()

        print(pnl2)


if __name__ == '__main__':
    main()
