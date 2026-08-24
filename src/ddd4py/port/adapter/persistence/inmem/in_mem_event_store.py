from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from injector import inject

from ddd4py.event import EventContextProvider, EventStore, StoredEvent

if TYPE_CHECKING:
    from ddd4py.domain.model import DomainEvent


class InMemEventStore(EventStore):
    @inject
    def __init__(self, context_provider: EventContextProvider):
        self.__context_provider = context_provider
        self.__stored_events: list[StoredEvent] = []

    @override
    def all_stored_events_between(self, from_stored_event_id: int, to_stored_event_id: int) -> list[StoredEvent]:
        return [e for e in self.__stored_events if from_stored_event_id <= e.event_id <= to_stored_event_id]

    @override
    def all_stored_events_since(self, stored_event_id: int) -> list[StoredEvent]:
        return [e for e in self.__stored_events if e.event_id > stored_event_id]

    @override
    def append(self, domain_event: DomainEvent) -> Self:
        context = self.__context_provider.context_of(domain_event)
        self.__stored_events.append(StoredEvent.new(len(self.__stored_events) + 1, domain_event, context))
        return self
