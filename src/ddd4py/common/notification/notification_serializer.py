from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddd4py.common.notification.notification import Notification


class NotificationSerializer:
    def __init__(self, publisher_name: str | None = None):
        self.__publisher_name = publisher_name

    def serialize(self, notification: Notification) -> str:
        notification_dict = notification.to_dict()
        notification_dict["publisher_name"] = notification_dict.get("publisher_name") or self.__publisher_name
        return json.dumps(notification_dict)
