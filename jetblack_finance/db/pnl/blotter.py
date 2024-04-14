"""A trade blotter"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Sequence, Tuple, cast

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from jetblack_finance.pnl import ITrade, ISplitTrade
from jetblack_finance.pnl.algorithm import add_split_trade
from jetblack_finance.pnl.pnl_state import PnlState
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
        pnl_state: Optional[PnlState] = None
    ) -> None:
        super().__init__(pnl_state)
        self._session = session
        self._instrument = instrument
        self._book = book

    def __add__(self, trade: Any) -> FifoPnl:
        assert isinstance(trade, Trade)
        split_trade = SplitTrade(trade=trade, used=Decimal(0))
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
        pnl_state: PnlState
    ) -> ABCPnl:
        return FifoPnl(
            self._session,
            self._instrument,
            self._book,
            pnl_state
        )

    def split_trade(self, trade: ITrade) -> ISplitTrade:
        return SplitTrade(trade=trade)

    def create_pnl(self, pnl_state: PnlState) -> PnlState:
        if pnl_state.unmatched:
            split_trade = pnl_state.unmatched[0]
        elif pnl_state.matched:
            _, split_trade = pnl_state.matched[0]
        else:
            raise ValueError('invalid state')

        self._session.add(
            Position(
                instrument=self._instrument,
                book=self._book,
                split_trade=split_trade,
                quantity=pnl_state.quantity,
                cost=pnl_state.cost,
                realized=pnl_state.realized
            )
        )
        self._session.commit()
        return pnl_state

    def push_unmatched(
            self,
            split_trade: ISplitTrade,
            unmatched: Sequence[ISplitTrade]
    ) -> Sequence[ISplitTrade]:
        unmatched_trade = UnmatchedTrade(split_trade=split_trade)
        self._session.add(unmatched_trade)
        return [split_trade] + list(unmatched)

    def pop_unmatched(
            self,
            unmatched: Sequence[ISplitTrade]
    ) -> Tuple[ISplitTrade, Sequence[ISplitTrade]]:
        split_trade, unmatched = unmatched[0], unmatched[1:]
        unmatched_trade = select(
            UnmatchedTrade
        ).where(
            UnmatchedTrade.split_trade == split_trade
        )
        self._session.delete(unmatched_trade)
        return split_trade, unmatched

    def push_matched(
            self,
            opening: ISplitTrade, closing: ISplitTrade,
            matched: Sequence[Tuple[ISplitTrade, ISplitTrade]]
    ) -> Sequence[Tuple[ISplitTrade, ISplitTrade]]:
        matched_trade = MatchedTrade(opening=opening, closing=closing)
        self._session.add(matched_trade)
        return list(matched) + [(opening, closing)]


class PnlFactory:

    def __init__(self, session: Session) -> None:
        self._session = session
        self._cache: Dict[Book, Dict[Instrument, FifoPnl]] = {}

    def __add__(self, other: Any) -> PnlFactory:
        assert isinstance(other, Trade)
        trade = cast(Trade, other)
        if trade.book_id not in self._cache:
            self._cache[trade.book] = {}
        by_instrument = self._cache[trade.book]
        if trade.instrument not in by_instrument:
            by_instrument[trade.instrument] = FifoPnl(
                self._session,
                trade.instrument,
                trade.book
            )
        pnl = by_instrument[trade.instrument]

        pnl = pnl + trade

        by_instrument[trade.instrument] = pnl

        return self


def main():
    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:

        pnl = PnlFactory(session)

        usd = Currency(
            ccy='USD',
            name='US Dollar',
            minor_unit=2,
            numeric_code=840
        )
        ibm = Instrument(name='IBM Inc', ccy=usd)
        tech_stocks = Book(name='tech stocks')
        big_bank = Counterparty(name='Big Bank')
        session.add_all([usd, ibm, tech_stocks, big_bank])
        session.commit()

        t1 = Trade(
            instrument=ibm,
            quantity=Decimal(100),
            price=Decimal(189.14),
            trade_date=date(2024, 4, 7),
            transaction_time=datetime(2024, 4, 7, 10, 17),
            ccy=usd,
            book=tech_stocks,
            counterparty=big_bank
        )
        session.add(t1)

        pnl1 = pnl + t1
        session.commit()

        t2 = Trade(
            instrument=ibm,
            quantity=Decimal(-50),
            price=Decimal(189.14),
            trade_date=date(2024, 4, 7),
            transaction_time=datetime(2024, 4, 7, 10, 18),
            ccy=usd,
            book=tech_stocks,
            counterparty=big_bank
        )
        session.add(t2)

        pnl2 = pnl1 + t2
        session.commit()

        t3 = Trade(
            instrument=ibm,
            quantity=Decimal(-50),
            price=Decimal(189.14),
            trade_date=date(2024, 4, 7),
            transaction_time=datetime(2024, 4, 7, 10, 18),
            ccy=usd,
            book=tech_stocks,
            counterparty=big_bank
        )
        session.add(t3)

        pnl3 = pnl2 + t3
        session.commit()

        print(pnl3)


if __name__ == '__main__':
    main()
