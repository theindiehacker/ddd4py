from __future__ import annotations

import abc
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SessionPreparer(abc.ABC):
    """Session を発行 / トランザクション開始した直後に実行文脈を適用するフック。

    マルチテナントの行レベルセキュリティ (RLS) を使う場合、ここで `SET LOCAL` 相当の
    GUC 設定を行う。トランザクションスコープに閉じるため、commit / rollback で自動復帰し、
    プールへ返却されたコネクションに設定が漏れない。

    既定は `NullSessionPreparer` (何もしない)。
    """

    @abc.abstractmethod
    def prepare(self, session: Session) -> None:
        """このセッションに実行文脈を適用する"""


class NullSessionPreparer(SessionPreparer):
    @override
    def prepare(self, session: Session) -> None:
        pass
