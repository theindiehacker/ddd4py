from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddd4py.notification.notification import Notification

# UUID4 を全体一致で強制 (version=4 / variant=[89ab], RFC 9562 §5.4)。
_UUID4_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


@dataclass(init=True)
class PublishedNotificationTracker:
    """どのイベントが発行済みであるかの記録。

    parameters:
     - tracker_id: このオブジェクトの一意な識別子
     - published_to: イベントの発行先のトピック / チャネル
     - most_recent_published_notification_id: 直近に発行された StoredEvent の event_id

    most_recent_published_notification_id と published_to があるので、任意の数のトピック /
    チャネルに対してそれぞれ異なるタイミングで同じ一連の通知を発行することもできる。
    """

    tracker_id: str
    published_to: str
    most_recent_published_notification_id: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PublishedNotificationTracker):
            return False
        return self.tracker_id == other.tracker_id

    def __hash__(self) -> int:
        return hash(self.tracker_id)

    def __post_init__(self) -> None:
        if not isinstance(self.tracker_id, str):
            raise TypeError(f"tracker_id には {type(self.tracker_id)} 型ではなく str 型を指定してください")
        # fullmatch で末尾改行・余剰文字を弾く。
        if _UUID4_PATTERN.fullmatch(self.tracker_id) is None:
            raise ValueError("tracker_id must be a UUID4.")
        if not isinstance(self.published_to, str):
            raise TypeError("published_to には str 型を指定してください")
        if not isinstance(self.most_recent_published_notification_id, int):
            raise TypeError("直近発行された通知 ID には int 型を指定してください")

    @staticmethod
    def new(published_to: str) -> PublishedNotificationTracker:
        return PublishedNotificationTracker(str(uuid.uuid4()), published_to, 0)

    def track(self, notifications: list[Notification]) -> None:
        """発行された通知一覧から発行記録を更新する"""
        if len(notifications) == 0:
            return
        latest = max(notifications, key=lambda notification: notification.occurred_on)
        self.most_recent_published_notification_id = latest.notification_id
