from __future__ import annotations

from dataclasses import dataclass


@dataclass(init=True, frozen=True)
class ConsumedNotification:
    """consume 済み通知の記録 (inbox)。

    redelivery (at-least-once 配送) されたイベントを二重処理しないための重複排除レコード。
    notification_id は発生元の StoredEvent.event_id で、境界内で一意のため重複排除キーに使う。

    重複排除のスコープは (consumer, listener, notification_id) の組。同一トピックを複数 consumer
    group が購読しても各 group が独立に処理でき、マルチ listener の部分失敗時には成功済み listener
    だけを skip して失敗 listener のみ再実行できるよう、consumer と listener を次元に含める。
    """

    consumer: str
    listener: str
    notification_id: int
    event_type: str

    def __post_init__(self) -> None:
        if not self.consumer:
            raise ValueError("consumer must not be empty")
        if not self.listener:
            raise ValueError("listener must not be empty")
        if not isinstance(self.notification_id, int):
            raise TypeError("notification_id must be an int")
        if not self.event_type:
            raise ValueError("event_type must not be empty")
