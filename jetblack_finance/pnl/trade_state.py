"""Trade state"""

from abc import abstractmethod
from typing import NamedTuple, Sequence

from .partial_trade import IPartialTrade


class TradeState(NamedTuple):

    unmatched: Sequence[IPartialTrade]

    matched: Sequence[tuple[IPartialTrade, IPartialTrade]]

    @abstractmethod
    def _push_unmatched(
        self,
        order: IPartialTrade,
        unmatched: Sequence[IPartialTrade]
    ) -> Sequence[IPartialTrade]:
        ...

    @abstractmethod
    def _pop_unmatched(
            self,
            unmatched: Sequence[IPartialTrade]
    ) -> tuple[IPartialTrade, Sequence[IPartialTrade]]:
        ...

    @abstractmethod
    def _push_matched(
            self,
            opening: IPartialTrade,
            closing: IPartialTrade,
            matched: Sequence[tuple[IPartialTrade, IPartialTrade]]
    ) -> Sequence[tuple[IPartialTrade, IPartialTrade]]:
        ...
