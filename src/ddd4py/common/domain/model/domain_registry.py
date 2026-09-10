from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING

from ddd4py.di import DIContainer

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


class DomainRegistry:
    """集約 / ドメインサービスから技術実装を解決するための窓口。

    集約がドメインサービスを必要とするとき、application 層に IF を渡させず
    `DomainRegistry.resolve(EncryptionService)` のように自分で解決する。
    """

    @staticmethod
    def resolve(interface: Callable[..., T]) -> T:
        return DIContainer.instance().resolve(interface)
