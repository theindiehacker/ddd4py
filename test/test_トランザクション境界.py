"""`@transactional` がトランザクション境界とドメインイベントの outbox 追記を握ることの検証。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import override

import pytest
from di import DI, DIContainer

from ddd4py.common import (
    ApplicationServiceLifeCycle,
    DomainEvent,
    DomainEventPublisher,
    EventContext,
    EventContextProvider,
    EventStore,
    NullEventContextProvider,
    UnitOfWork,
    transactional,
)
from ddd4py.common.port.adapter.persistence.inmem import InMemEventStore
from ddd4py.common.testing import reset_di_container


@dataclass(init=True, unsafe_hash=True, frozen=True)
class ユーザー登録済み(DomainEvent):
    user_id: str = ""

    @override
    def to_dict(self) -> dict:
        return {"user_id": self.user_id}


class 記録するUnitOfWork(UnitOfWork[object]):
    def __init__(self) -> None:
        self.操作: list[str] = []

    @override
    def mark(self, instance: object) -> None: ...

    @override
    def persist(self, instance: object) -> None: ...

    @override
    def delete(self, *instances: object) -> None: ...

    @override
    def start(self) -> None:
        self.操作.append("start")

    @override
    def flush(self) -> None:
        self.操作.append("flush")

    @override
    def rollback(self) -> None:
        self.操作.append("rollback")

    @override
    def commit(self) -> None:
        self.操作.append("commit")


@pytest.fixture
def unit_of_work() -> Iterator[記録するUnitOfWork]:
    # injector の singleton は束縛ごとにインスタンスをキャッシュするため、テストごとに破棄する
    reset_di_container()
    uow = 記録するUnitOfWork()
    event_store = InMemEventStore(NullEventContextProvider())
    DIContainer.instance().register(
        DI.of(UnitOfWork, {}, uow),
        DI.of(EventContextProvider, {}, NullEventContextProvider()),
        DI.of(EventStore, {}, event_store),
        DI.of(ApplicationServiceLifeCycle, {}, ApplicationServiceLifeCycle(uow, event_store)),
    )
    yield uow
    reset_di_container()


def test_成功したユースケースはcommitされる(unit_of_work: 記録するUnitOfWork) -> None:
    @transactional
    def 登録する() -> str:
        return "ok"

    assert 登録する() == "ok"
    assert unit_of_work.操作 == ["start", "commit"]


def test_失敗したユースケースはrollbackされ例外が伝播する(unit_of_work: 記録するUnitOfWork) -> None:
    @transactional
    def 失敗する() -> None:
        raise ValueError("業務エラー")

    with pytest.raises(ValueError, match="業務エラー"):
        失敗する()
    assert unit_of_work.操作 == ["start", "rollback"]


def test_ネストした境界は最外だけがcommitする(unit_of_work: 記録するUnitOfWork) -> None:
    @transactional
    def 内側() -> None: ...

    @transactional
    def 外側() -> None:
        内側()

    外側()
    # 内側の start は join し、commit は最外の 1 回だけ
    assert unit_of_work.操作 == ["start", "start", "commit"]


def test_ネスト内の失敗は最外まで巻き戻る(unit_of_work: 記録するUnitOfWork) -> None:
    @transactional
    def 内側() -> None:
        raise ValueError("内側で失敗")

    @transactional
    def 外側() -> None:
        内側()

    with pytest.raises(ValueError, match="内側で失敗"):
        外側()
    # 内側の rollback で深さが 0 に戻るため、外側の rollback は空 rollback となり無害
    assert unit_of_work.操作 == ["start", "start", "rollback", "rollback"]
    assert "commit" not in unit_of_work.操作


def test_境界内でpublishしたイベントがoutboxに追記される(unit_of_work: 記録するUnitOfWork) -> None:
    event_store: EventStore = DIContainer.instance().resolve(EventStore)

    @transactional
    def 登録する() -> None:
        DomainEventPublisher.instance().publish(ユーザー登録済み(1, user_id="u-1"))

    登録する()

    stored = event_store.all_stored_events_since(0)
    assert len(stored) == 1
    assert stored[0].event_type == "ユーザー登録済み.1"
    assert stored[0].event_body == {"user_id": "u-1"}
    assert stored[0].partition_key == EventContext.DEFAULT_PARTITION_KEY


def test_境界を抜けた後のpublishはoutboxに漏れない(unit_of_work: 記録するUnitOfWork) -> None:
    event_store: EventStore = DIContainer.instance().resolve(EventStore)

    @transactional
    def 登録する() -> None: ...

    登録する()
    DomainEventPublisher.instance().publish(ユーザー登録済み(1, user_id="u-2"))

    assert event_store.all_stored_events_since(0) == []
