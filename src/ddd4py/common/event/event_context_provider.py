from __future__ import annotations

import abc
from contextlib import contextmanager
from typing import TYPE_CHECKING, override

from ddd4py.common.domain.model import EventContext

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager

    from ddd4py.common.domain.model import DomainEvent


class EventContextProvider(abc.ABC):
    """アンビエントな実行文脈の読み書きを担う唯一のポート。

    - `current()`: いま処理中の文脈を読む (outbox への刻印時に使う)
    - `bind()`: 受信した文脈を確立する (inbox の dispatch 時に使う)

    マルチテナントなアプリは「いま処理中のテナント / プレーン」を返す実装を DI 登録する。
    単一テナントなら `NullEventContextProvider` のままでよい。

    カーネルが実行文脈そのもの (リクエストスコープの ContextVar 等) を持たないのは、
    文脈の語彙が利用側ごとに違うため。カーネルは「刻印する / 確立する」ことだけを知っている。
    """

    @abc.abstractmethod
    def current(self) -> EventContext:
        """いま処理中の実行文脈を返す"""

    @abc.abstractmethod
    def bind(self, context: EventContext) -> AbstractContextManager[None]:
        """受信した文脈を、ブロックの間だけ確立する"""

    def context_of(self, domain_event: DomainEvent) -> EventContext:
        """イベントに刻印する文脈を決める。

        既定は発生元 (append 時点の文脈)。境界をまたぐイベントだけが
        `DomainEvent.routing_context()` で処理先を自己申告し、それが優先される。
        """
        return domain_event.routing_context() or self.current()


class NullEventContextProvider(EventContextProvider):
    """単一テナント / 単一プレーン向けの既定実装。文脈を持たず、常に既定値を返す。"""

    @override
    def current(self) -> EventContext:
        return EventContext()

    @override
    @contextmanager
    def bind(self, context: EventContext) -> Iterator[None]:
        yield
