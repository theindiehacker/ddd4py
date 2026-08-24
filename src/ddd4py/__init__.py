"""モジュラモノリス + DDD のカーネル。"""

from importlib.metadata import version

from ddd4py.application import ApplicationServiceLifeCycle, UnitOfWork, transactional
from ddd4py.domain.model import (
    DomainEvent,
    DomainEventPublisher,
    DomainEventSubscriber,
    DomainRegistry,
    EventContext,
)
from ddd4py.event import EventContextProvider, EventStore, NullEventContextProvider, StoredEvent
from ddd4py.exception import CoreCode, ErrorCode, ErrorLevel, SystemException
from ddd4py.module import AppModule, CompositeModule
from ddd4py.settings import BaseAppSettings, CoreSettings

# バージョンの真実源は pyproject.toml の [project].version 一箇所。
# 引数は import 名ではなく配布名 (どちらも ddd4py)。
__version__ = version("ddd4py")

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
    "__version__",
    "transactional",
]
