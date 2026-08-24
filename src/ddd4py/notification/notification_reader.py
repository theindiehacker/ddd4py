from __future__ import annotations

import json


class NotificationReader:
    """受信した通知 JSON からドット区切りのパスで値を取り出す。"""

    def __init__(self, json_notification: str):
        self.__json: dict = json.loads(json_notification)

    def event_str_value(self, keys: str) -> str | None:
        return self.__str_value(keys)

    def event_bool_value(self, keys: str) -> bool | None:
        optional = self.__str_value(keys)
        return None if optional is None else optional.lower() in {"true", "1"}

    def event_int_value(self, keys: str) -> int | None:
        optional = self.__str_value(keys)
        return None if optional is None else int(optional)

    def event_float_value(self, keys: str) -> float | None:
        optional = self.__str_value(keys)
        return None if optional is None else float(optional)

    def __str_value(self, keys: str) -> str | None:
        value: object = self.__json
        for key in keys.split("."):
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return None if value is None else str(value)
