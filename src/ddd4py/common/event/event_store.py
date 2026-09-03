from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ddd4py.common.domain.model import DomainEvent
    from ddd4py.common.event.stored_event import StoredEvent


class EventStore(abc.ABC):
    """outbox。`@transactional` の内側で DomainEvent を StoredEvent として追記する。"""

    @abc.abstractmethod
    def all_stored_events_between(self, from_stored_event_id: int, to_stored_event_id: int) -> list[StoredEvent]:
        pass

    @abc.abstractmethod
    def all_stored_events_since(self, stored_event_id: int) -> list[StoredEvent]:
        pass

    @abc.abstractmethod
    def append(self, domain_event: DomainEvent) -> Self:
        pass
