"""カーネル同梱の適合テストキットが、同梱の InMem 実装に対して通ることの検証。

利用側プロジェクトはこれと同じ関数を、自分の PostgreSQL / Redis 実装に対して走らせる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ddd4py.common import DomainEvent, NullEventContextProvider
from ddd4py.common.port.adapter.persistence.inmem import (
    InMemConsumedNotificationStore,
    InMemEventStore,
    InMemPublishedNotificationTrackerStore,
    InMemUnitOfWork,
)
from ddd4py.common.testing import (
    verify_consumed_notification_store,
    verify_event_store,
    verify_published_notification_tracker_store,
    verify_unit_of_work,
)


@dataclass(init=True, unsafe_hash=True, frozen=True)
class 何かが起きた(DomainEvent):
    @override
    def to_dict(self) -> dict:
        return {}


def test_InMemUnitOfWorkはUnitOfWorkの契約を満たす() -> None:
    verify_unit_of_work(InMemUnitOfWork())


def test_InMemEventStoreはEventStoreの契約を満たす() -> None:
    verify_event_store(InMemEventStore(NullEventContextProvider()), lambda: 何かが起きた(1))


def test_InMemConsumedNotificationStoreはinboxの契約を満たす() -> None:
    verify_consumed_notification_store(InMemConsumedNotificationStore())


def test_InMemPublishedNotificationTrackerStoreは発行記録の契約を満たす() -> None:
    verify_published_notification_tracker_store(InMemPublishedNotificationTrackerStore())
