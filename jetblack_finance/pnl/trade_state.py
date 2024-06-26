"""Trade state"""

from abc import abstractmethod
from typing import NamedTuple, Sequence, Tuple

from .split_trade import ISplitTrade


class TradeState(NamedTuple):

    unmatched: Sequence[ISplitTrade]

    matched: Sequence[Tuple[ISplitTrade, ISplitTrade]]

    @abstractmethod
    def _push_unmatched(
        self,
        order: ISplitTrade,
        unmatched: Sequence[ISplitTrade]
    ) -> Sequence[ISplitTrade]:
        ...

    @abstractmethod
    def _pop_unmatched(
            self,
            unmatched: Sequence[ISplitTrade]
    ) -> tuple[ISplitTrade, Sequence[ISplitTrade]]:
        ...

    @abstractmethod
    def _push_matched(
            self,
            opening: ISplitTrade,
            closing: ISplitTrade,
            matched: Sequence[Tuple[ISplitTrade, ISplitTrade]]
    ) -> Sequence[Tuple[ISplitTrade, ISplitTrade]]:
        ...
