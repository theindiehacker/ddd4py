from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import timedelta

    from ddd4py.notification.consumed_notification import ConsumedNotification


class ConsumedNotificationStore(abc.ABC):
    """consume 済み通知 (inbox) の重複排除ストア (transactional inbox)。

    `claim` で notification を listener 単位に席取りし、取れた配送だけが処理する
    (claim-before-process)。
    """

    @abc.abstractmethod
    def claim(self, consumed_notification: ConsumedNotification) -> bool:
        """notification を claim する。新規に claim できれば True、既に claim 済み
        (= 重複 / 同時再配送) なら False を返す。

        claim は ambient な UnitOfWork トランザクションに参加し、marker と listener の副作用が
        単一トランザクションとして commit される (rollback すれば claim ごと巻き戻り、再配送で
        再試行できる)。同時到達の重複は unique 制約の挿入行ロックで先勝ち 1 つに絞られる。
        """

    @abc.abstractmethod
    def prune(self, retention: timedelta) -> int:
        """保持期間 (retention) を超過した consumed marker を一括削除し、削除件数を返す。

        marker は重複判定の期間だけ参照される短命データのため、定期 prune で retention を代替する。
        retention は再配送ホライズン (例: Pub/Sub のメッセージ保持 7 日) より長く取ること。
        短いと「prune 後の再配送」を新規 claim できてしまい二重処理になる。
        """
