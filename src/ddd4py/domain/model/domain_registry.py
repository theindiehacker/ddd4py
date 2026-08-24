from __future__ import annotations

from typing import TYPE_CHECKING

from di import DIContainer

if TYPE_CHECKING:
    from injector import T


class DomainRegistry:
    """集約 / ドメインサービスから技術実装を解決するための窓口。

    集約がドメインサービスを必要とするとき、application 層に IF を渡させず
    `DomainRegistry.resolve(EncryptionService)` のように自分で解決する。
    """

    @staticmethod
    def resolve(interface: type[T]) -> T:
        return DIContainer.instance().resolve(interface)
