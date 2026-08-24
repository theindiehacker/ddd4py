from __future__ import annotations

from typing import TYPE_CHECKING, override

from ddd4py.notification import ConsumedNotificationStore

if TYPE_CHECKING:
    from datetime import timedelta

    from ddd4py.notification import ConsumedNotification


class InMemConsumedNotificationStore(ConsumedNotificationStore):
    def __init__(self) -> None:
        self.__claimed: set[ConsumedNotification] = set()

    @override
    def claim(self, consumed_notification: ConsumedNotification) -> bool:
        if consumed_notification in self.__claimed:
            return False
        self.__claimed.add(consumed_notification)
        return True

    @override
    def prune(self, retention: timedelta) -> int:
        # メモリ実装は経過時間を持たないため、prune では何も消さない (契約上 0 件は合法)。
        return 0
