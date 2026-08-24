from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddd4py.notification import Notification


class MessagePublisher(abc.ABC):
    @abc.abstractmethod
    def publish(self, to: str, notification: Notification) -> None:
        pass
