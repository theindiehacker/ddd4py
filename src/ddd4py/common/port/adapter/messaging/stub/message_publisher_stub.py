from __future__ import annotations

from typing import TYPE_CHECKING, override

from ddd4py.common.port.adapter.messaging.message_publisher import MessagePublisher

if TYPE_CHECKING:
    from ddd4py.common.notification import Notification


class MessagePublisherStub(MessagePublisher):
    """発行内容をメモリに記録するだけのスタブ。テストで発行の有無を検証するのに使う。"""

    def __init__(self) -> None:
        self.published: list[tuple[str, Notification]] = []

    @override
    def publish(self, to: str, notification: Notification) -> None:
        self.published.append((to, notification))
