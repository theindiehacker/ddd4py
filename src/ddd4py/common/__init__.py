"""モジュラモノリス + DDD のカーネル (共通モジュール)。"""

from ddd4py.common.application import ApplicationServiceLifeCycle, UnitOfWork, transactional
from ddd4py.common.domain.model import (
    DomainEvent,
    DomainEventPublisher,
    DomainEventSubscriber,
    DomainRegistry,
    EventContext,
)
from ddd4py.common.event import EventContextProvider, EventStore, NullEventContextProvider, StoredEvent
from ddd4py.common.exception import CoreCode, ErrorCode, ErrorLevel, SystemException
from ddd4py.common.module import AppModule, CompositeModule
from ddd4py.common.settings import BaseAppSettings, CoreSettings

__all__ = [
    "AppModule",
    "ApplicationServiceLifeCycle",
    "BaseAppSettings",
    "CompositeModule",
    "CoreCode",
    "CoreSettings",
    "DomainEvent",
    "DomainEventPublisher",
    "DomainEventSubscriber",
    "DomainRegistry",
    "ErrorCode",
    "ErrorLevel",
    "EventContext",
    "EventContextProvider",
    "EventStore",
    "NullEventContextProvider",
    "StoredEvent",
    "SystemException",
    "UnitOfWork",
    "transactional",
]
