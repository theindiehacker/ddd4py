from __future__ import annotations

from typing import TypeVar

from ddd4py.di import DIContainer

T = TypeVar("T")


class DomainRegistry:
    """集約 / ドメインサービスから技術実装を解決するための窓口。

    集約がドメインサービスを必要とするとき、application 層に IF を渡させず
    `DomainRegistry.resolve(EncryptionService)` のように自分で解決する。
    """

    @staticmethod
    def resolve(interface: type[T]) -> T:
        return DIContainer.instance().resolve(interface)
