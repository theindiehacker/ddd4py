from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import datetime

    from ddd4py.event import StoredEvent


@dataclass(init=True, eq=False)
class Notification:
    """outbox の StoredEvent を MQ へ載せるための転送表現。"""

    notification_id: int
    event: dict
    occurred_on: datetime.datetime
    publisher: str
    event_type: str
    version: int
    # 処理境界のキー (StoredEvent.partition_key 由来)。subscriber が処理文脈を解決するための
    # メタデータで、publisher は MQ の属性 (Pub/Sub attributes / SNS MessageAttributes) にも載せる。
    partition_key: str
    context: dict

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Notification):
            return False
        return other.notification_id == self.notification_id

    def __hash__(self) -> int:
        return hash(("Notification", self.notification_id))

    @staticmethod
    def of(stored_event: StoredEvent) -> Notification:
        if stored_event.event_id is None:
            raise ValueError("Notification は採番済みの StoredEvent からのみ生成できます")
        return Notification(
            stored_event.event_id,
            stored_event.event_body,
            stored_event.occurred_on,
            stored_event.publisher,
            stored_event.event_type,
            stored_event.version,
            stored_event.partition_key,
            stored_event.context,
        )

    def to_dict(self) -> dict:
        """シリアライズする際に利用する"""
        return {
            "notification_id": self.notification_id,
            "event": self.event,
            "occurred_on": self.occurred_on.strftime("%Y-%m-%d %H:%M:%S"),
            "publisher_name": self.publisher,
            "event_type": self.event_type,
            "version": self.version,
            "partition_key": self.partition_key,
            "context": self.context,
        }


class NotificationJson[T](TypedDict):
    notification_id: int
    event: T
    occurred_on: str
    event_type: str
    version: int
    publisher_name: str
    partition_key: str
    context: dict
