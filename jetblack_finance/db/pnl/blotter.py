"""A trade blotter"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional, cast

from mariadb.connections import Connection
from mariadb.cursors import Cursor

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from jetblack_finance.pnl import ITrade, ISplitTrade
from jetblack_finance.pnl.pnl_state import PnlState
from jetblack_finance.pnl.pnl_implementations import ABCPnl, Matched, Unmatched


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


def make_split_trade_factory(session: Session):

    def split_trade_factory(trade: ITrade) -> ISplitTrade:
        split_trade = SplitTrade(trade=trade, used=Decimal(0))
        session.add(split_trade)
        return split_trade

    return split_trade_factory


class FifoPnl(PnlState):

    def __init__(
        self,
        quantity=Decimal(0),
        cost=Decimal(0),
        realized=Decimal(0),
        unmatched: Optional[Unmatched] = None,
        matched: Optional[Matched] = None,
        session: Session
    ) -> None:
        super().__init__(
            quantity,
            cost,
            realized,
            unmatched or [],
            matched or [],
        )
        self._factory = factory or SplitTrade

    def __add__(self, other: Any) -> ABCPnl:
        assert isinstance(other, ITrade)
        split_trade = self._factory(other)
        state = add_split_trade(
            self,
            split_trade,
            self._push_unmatched,
            self._pop_unmatched,
            self._push_matched
        )
        return self._create(state)

    def _create(
        self,
        state: PnlState
    ) -> FifoPnl:
        return FifoPnl(
            state.quantity,
            state.cost,
            state.realized,
            state.unmatched,
            state.matched,
            lambda trade: SplitTrade(trade=trade)
        )

    def _pop_unmatched(self, unmatched: Unmatched) -> tuple[ISplitTrade, Unmatched]:
        return unmatched[0], unmatched[1:]

    def _push_unmatched(self, split_trade: ISplitTrade, unmatched: Unmatched) -> Unmatched:
        UnmatchedTrade(split_trade=split_trade)
        return [split_trade] + list(unmatched)

    def _push_matched(self, opening: ISplitTrade, closing: ISplitTrade, matched: Matched) -> Matched:
        return list(matched) + [MatchedTrade(opening, closing)]


def main():
    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        pnl = FifoPnl(factory=make_split_trade_factory(session))

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

        pnl2 = pnl + t1
        session.commit()

        print(pnl2)


if __name__ == '__main__':
    main()
