from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddd4py.common.notification.published_notification_tracker import PublishedNotificationTracker


class PublishedNotificationTrackerStore(abc.ABC):
    @abc.abstractmethod
    def published_notification_tracker_of(self, published_to: str) -> PublishedNotificationTracker:
        """イベントの発行先のトピック / チャネル指定で発行済み通知のトラッカーを取得する"""

    @abc.abstractmethod
    def track_most_recent_published_notification(self, tracker: PublishedNotificationTracker) -> None:
        """発行した通知一覧から発行済みトラッカーを更新する"""
