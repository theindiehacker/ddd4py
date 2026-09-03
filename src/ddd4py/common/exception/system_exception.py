from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddd4py.common.exception.error_code import ErrorCode


class SystemException(RuntimeError):
    def __init__(self, error_code: ErrorCode, detail: str):
        super().__init__(f"{error_code.name}: {detail}")
        self.error_code = error_code
        self.detail = detail

    def logging(self) -> None:
        self.error_code.log(self.detail)
