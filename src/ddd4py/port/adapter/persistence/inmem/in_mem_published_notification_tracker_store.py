from __future__ import annotations

from typing import override

from ddd4py.notification import PublishedNotificationTracker, PublishedNotificationTrackerStore


class InMemPublishedNotificationTrackerStore(PublishedNotificationTrackerStore):
    def __init__(self) -> None:
        self.__trackers: dict[str, PublishedNotificationTracker] = {}

    @override
    def published_notification_tracker_of(self, published_to: str) -> PublishedNotificationTracker:
        if published_to not in self.__trackers:
            self.__trackers[published_to] = PublishedNotificationTracker.new(published_to)
        return self.__trackers[published_to]

    @override
    def track_most_recent_published_notification(self, tracker: PublishedNotificationTracker) -> None:
        self.__trackers[tracker.published_to] = tracker
