from __future__ import annotations

import functools
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, override

from di import DIContainer
from injector import inject, singleton

from ddd4py.common.application.unit_of_work import UnitOfWork
from ddd4py.common.domain.model import DomainEvent, DomainEventPublisher, DomainEventSubscriber
from ddd4py.common.event import EventStore

if TYPE_CHECKING:
    from collections.abc import Callable

# トランザクション境界のネスト深さ。subscriber の dispatch トランザクション内から listener が
# `@transactional` な ApplicationService を呼ぶと境界が入れ子になるため、最外の境界だけが
# commit / rollback するよう深さを追跡する (UoW の start 自体は in_transaction() で join 済み)。
# ApplicationServiceLifeCycle は singleton のため、実行コンテキストごとの深さは ContextVar に持つ。
_transaction_depth: ContextVar[int] = ContextVar("ddd4py_transaction_depth", default=0)


class _EventStoreSubscriber(DomainEventSubscriber[DomainEvent]):
    """publish された全ドメインイベントを outbox に追記する購読者。"""

    def __init__(self, event_store: EventStore):
        self.__event_store = event_store

    @override
    def subscribed_to_event_type(self) -> type[DomainEvent]:
        return DomainEvent

    @override
    def handle_event(self, domain_event: DomainEvent) -> None:
        self.__event_store.append(domain_event)


@singleton
class ApplicationServiceLifeCycle:
    """`@transactional` の実体。トランザクション境界とドメインイベント購読の生存期間を握る。"""

    @inject
    def __init__(self, unit_of_work: UnitOfWork, event_store: EventStore):
        self.__unit_of_work = unit_of_work
        self.__event_store = event_store

    def begin(self, is_listening: bool = True) -> None:
        if is_listening:
            self.listen()
        self.__unit_of_work.start()
        _transaction_depth.set(_transaction_depth.get() + 1)

    def fail(self, exception: Exception | None = None) -> None:
        """ネスト中の失敗も最外までトランザクション全体を巻き戻す (部分 commit を許さない)。

        内側の fail で深さを 0 に戻すため、伝播後の外側 fail の rollback は新規セッションへの
        空 rollback となり無害。

        前提: ネスト内の失敗は必ず最外境界まで伝播させること (握り潰し禁止)。内側の例外を catch
        して処理を続行すると、最外の success() は depth=0 の空 commit となり、副作用も consumed
        marker も確定しないまま成功扱い (ack) になって配送が静かに失われる。
        """
        _transaction_depth.set(0)
        self.__unit_of_work.rollback()
        # トランザクション境界を抜ける際に購読者を破棄する。残したまま @transactional の外で
        # DomainEventPublisher.publish が呼ばれると、EventStore subscriber が UnitOfWork の
        # セッションに書き込んでしまい、後続処理へトランザクション状態が漏れる。
        DomainEventPublisher.instance().reset()
        if exception is not None:
            raise exception

    def success(self) -> None:
        depth = _transaction_depth.get()
        if depth > 1:
            # ネストした内側の境界は commit せず、最外の境界に委ねる。
            _transaction_depth.set(depth - 1)
            return
        try:
            self.__unit_of_work.commit()
        finally:
            _transaction_depth.set(0)
            DomainEventPublisher.instance().reset()

    def listen(self) -> None:
        DomainEventPublisher.instance().reset()
        DomainEventPublisher.instance().subscribe(_EventStoreSubscriber(self.__event_store))


def _dynamic_args(deco_func: Callable[..., Any]) -> Callable[..., Any]:
    # デコレータは任意のシグネチャの関数を包むため、引数型は本質的に Any になる。
    def wrapper(*args: Any, **kwargs: Any) -> Callable[..., Any]:  # noqa: ANN401
        if len(args) != 0 and callable(args[0]):
            # 第一引数に関数が渡された場合: 引数なしのデコレータとして扱う
            return functools.wraps(args[0])(deco_func(args[0]))

        def _wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            return functools.wraps(func)(deco_func(func, *args, **kwargs))

        return _wrapper

    return wrapper


@_dynamic_args
def transactional[T](method: Callable[..., T], is_listening: bool = True) -> Callable[..., T]:
    """AOP によるトランザクション管理を行うためのデコレータ"""

    @functools.wraps(method)
    def handle_transaction(*args: Any, **kwargs: Any) -> T:  # type: ignore[return]  # noqa: ANN401
        life_cycle: ApplicationServiceLifeCycle = DIContainer.instance().resolve(ApplicationServiceLifeCycle)
        life_cycle.begin(is_listening)
        try:
            _return = method(*args, **kwargs)
            life_cycle.success()
        except Exception as e:  # noqa: BLE001
            life_cycle.fail(e)
        else:
            return _return

    return handle_transaction
