"""カーネルが業務語彙を持たずに実行文脈を刻印できることの検証。

`EventContextProvider` が唯一の接点で、テナント / App といった語彙は利用側にある。
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import pytest

from ddd4py import DomainEvent, EventContext, EventContextProvider, NullEventContextProvider, StoredEvent
from ddd4py.port.adapter.persistence.inmem import InMemEventStore

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(init=True, unsafe_hash=True, frozen=True)
class テナント作成済み(DomainEvent):
    tenant_id: str = ""

    @override
    def to_dict(self) -> dict:
        return {"tenant_id": self.tenant_id}


@dataclass(init=True, unsafe_hash=True, frozen=True)
class 別境界で処理すべきイベント(DomainEvent):
    @override
    def to_dict(self) -> dict:
        return {}

    @override
    def routing_context(self) -> EventContext:
        return EventContext("acme", {"tenant": "acme"})


class テナント文脈(EventContextProvider):
    """利用側が自分の語彙をカーネルの 2 値に翻訳する実装の例。"""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.bound: list[EventContext] = []

    @override
    def current(self) -> EventContext:
        return EventContext(self.tenant_id, {"tenant": self.tenant_id})

    @override
    @contextmanager
    def bind(self, context: EventContext) -> Iterator[None]:
        self.bound.append(context)
        yield


def test_発生元の文脈がoutboxに刻印される() -> None:
    event_store = InMemEventStore(テナント文脈("shibuya"))
    event_store.append(テナント作成済み(1, tenant_id="t-1"))

    stored = event_store.all_stored_events_since(0)[0]
    assert stored.partition_key == "shibuya"
    assert stored.context == {"tenant": "shibuya"}


def test_境界をまたぐイベントは処理先を自己申告できる() -> None:
    event_store = InMemEventStore(テナント文脈("shibuya"))
    event_store.append(別境界で処理すべきイベント(1))

    stored = event_store.all_stored_events_since(0)[0]
    assert stored.partition_key == "acme", "routing_context() の申告が発生元より優先されるべき"


def test_文脈を持たないアプリは既定値で動く() -> None:
    event_store = InMemEventStore(NullEventContextProvider())
    event_store.append(テナント作成済み(1, tenant_id="t-1"))

    assert event_store.all_stored_events_since(0)[0].partition_key == EventContext.DEFAULT_PARTITION_KEY


def test_イベントタイプは発行元モジュールを含む() -> None:
    stored = StoredEvent.new(1, テナント作成済み(2, tenant_id="t-1"), EventContext())
    assert stored.type == "test.テナント作成済み.2"
    assert stored.publisher == "test"
    assert stored.event_type == "テナント作成済み.2"
    assert stored.version == 2


def test_不正なイベントタイプは拒否される() -> None:
    with pytest.raises(ValueError, match="Invalid event type"):
        StoredEvent(1, "壊れたタイプ", {}, テナント作成済み(1).occurred_on, "default", {})


def test_partition_keyが空の文脈は作れない() -> None:
    with pytest.raises(ValueError, match="partition_key must not be empty"):
        EventContext("", {})
