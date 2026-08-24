from __future__ import annotations

from typing import override

from ddd4py.application import UnitOfWork


class InMemUnitOfWork(UnitOfWork[object]):
    """永続化しない UnitOfWork。ユニットテスト / ドメイン層のみの検証で使う。"""

    @override
    def mark(self, instance: object) -> None:
        pass

    @override
    def persist(self, instance: object) -> None:
        pass

    @override
    def delete(self, *instances: object) -> None:
        pass

    @override
    def start(self) -> None:
        pass

    @override
    def flush(self) -> None:
        pass

    @override
    def rollback(self) -> None:
        pass

    @override
    def commit(self) -> None:
        pass
