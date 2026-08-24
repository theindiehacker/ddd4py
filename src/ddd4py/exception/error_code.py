from __future__ import annotations

import logging
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    WARN = ("WARN", logger.warning)
    ERROR = ("ERROR", logger.error)
    CRITICAL = ("CRITICAL", logger.critical)

    def __init__(self, level: str, logging_: Callable[[str], None]):
        self.level = level
        self.__logging = logging_

    def to_logger(self, error_code: ErrorCode, detail: str) -> None:
        self.__logging(f"[Code] {error_code.name} [Message] {error_code.message} [Detail] {detail}")


class ErrorCode(Enum):
    """業務エラーの分類。利用側プロジェクトはこれを継承して自分のコード体系を定義する。

    継承先の例:
        class AuthorityCode(ErrorCode):
            USER_NOT_FOUND = ("ユーザーが見つかりません", ErrorLevel.WARN, HTTPStatus.NOT_FOUND)
    """

    def __init__(self, message: str, error_level: ErrorLevel, http_status: HTTPStatus):
        self.message = message
        self.error_level = error_level
        self.http_status = http_status

    def log(self, detail: str) -> None:
        self.error_level.to_logger(self, detail)


class CoreCode(ErrorCode):
    """カーネル自身が送出するエラー。業務エラーは利用側が ErrorCode を継承して定義する。"""

    CORE_1000 = ("想定外の原因エラーが発生しました", ErrorLevel.ERROR, HTTPStatus.INTERNAL_SERVER_ERROR)
    # 実行文脈 (テナント境界など) が未解決のままデータアクセスしようとした防衛発火 (fail-closed)。
    # 汎用の 1000 と分けることで、監視で境界違反の発火だけを切り分けてカウントできる。
    CORE_1001 = ("実行文脈が未解決のため処理を拒否しました", ErrorLevel.ERROR, HTTPStatus.INTERNAL_SERVER_ERROR)
