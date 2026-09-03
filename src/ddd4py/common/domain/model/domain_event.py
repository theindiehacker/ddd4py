from __future__ import annotations

import abc
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Self

import pytz

if TYPE_CHECKING:
    from ddd4py.common.domain.model.event_context import EventContext


@dataclass(init=True, unsafe_hash=True, frozen=True)
class DomainEvent(abc.ABC):
    """ドメインイベント"""

    event_version: int
    occurred_on: datetime = field(default_factory=lambda: datetime.now(pytz.timezone("Asia/Tokyo")))

    def __post_init__(self) -> None:
        if self.event_version is None or self.event_version < 0:
            raise ValueError("event_version must be >= 0")
        if self.occurred_on is None or not isinstance(self.occurred_on, datetime):
            raise ValueError("occurred_on must be set")

    @property
    def type(self) -> str:
        return f"{self.__class__.__name__}.{self.event_version}"

    @abc.abstractmethod
    def to_dict(self) -> dict:
        """MQ のペイロードとして送信する JSON 形式の値を指定する"""

    def routing_context(self) -> EventContext | None:
        """イベントを処理すべき文脈の自己申告。既定 (None) は発生元 (append 時点の文脈)。

        境界をまたぐ副作用を起こすイベントだけが override する。申告すると全購読者が申告先の
        文脈で処理される点に注意 (発生元でも副作用が要るなら、別イベントに分けること)。
        """
        return None


class DomainEventPublisher(threading.local):
    """スレッドローカルなドメインイベントパブリッシャー

    シングルトンのインスタンス自体は共有されるが、内部データは threading.local により
    スレッドごとに分離される。
    """

    _instance: DomainEventPublisher | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        super().__init__()
        self.__subscribers: set[DomainEventSubscriber] = set()

    @classmethod
    def instance(cls) -> DomainEventPublisher:
        """スレッドセーフなシングルトンインスタンス取得"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = DomainEventPublisher()
        return cls._instance

    def reset(self) -> Self:
        self.__subscribers = set()
        return self

    def publish(self, domain_event: DomainEvent) -> None:
        for subscriber in self.__subscribers:
            if isinstance(domain_event, subscriber.subscribed_to_event_type()):
                subscriber.handle_event(domain_event)

    def subscribe(self, subscriber: DomainEventSubscriber) -> None:
        self.__subscribers.add(subscriber)


class DomainEventSubscriber[T](abc.ABC):
    """サブスクライバー"""

    @abc.abstractmethod
    def handle_event(self, domain_event: T) -> None:
        pass

    @abc.abstractmethod
    def subscribed_to_event_type(self) -> type[T]:
        pass
