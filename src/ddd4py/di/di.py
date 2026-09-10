from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from injector import Binder, Module, singleton

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")

# binder.bind(to=...) に渡せるもの。クラスでもインスタンスでもよい (injector 側が判別する)。
Bindable = Any


@dataclass(init=True, frozen=True)
class Profile:
    """束縛を有効にする条件。有効化されたプロファイル名をすべて含むときにマッチする。"""

    values: set[str]

    def match(self, actives: set[str]) -> bool:
        return all(name in actives for name in self.values)

    def __hash__(self) -> int:
        # set は順序を持たないため、ソートしてからハッシュ化する
        return hash(str(sorted(self.values)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Profile):
            return False
        return self.values == other.values


class Switcher:
    """有効なプロファイルに応じて束縛先を選ぶ。どれにもマッチしなければ既定へ落とす。"""

    @classmethod
    def get(cls, classes: dict[Profile, Bindable], default: Bindable) -> Bindable:
        # 環境変数はクラス変数に持たせず毎回読む。import 時に評価すると .env の読み込みや
        # テストの monkeypatch が反映されず、本物の実装のつもりが静かに既定へ落ちる。
        # 空文字列を落としているのは "".split(",") が [""] を返すため (未設定を空集合にする)。
        actives = {name.strip() for name in os.getenv("DI_FOR_PY", "").split(",") if name.strip()}
        for profile, a_class in classes.items():
            if profile.match(actives):
                return a_class
        return default


@dataclass(init=True, frozen=False, unsafe_hash=True)
class DI(Module):
    """1 つの interface に対する束縛の宣言。DIContainer へ register して使う。"""

    interface: Callable[..., Any]
    classes: dict[Profile, Bindable]
    default: Bindable

    @staticmethod
    def of(interface: Callable[..., T], classes: dict[str, Bindable], default: Bindable) -> DI:
        """プロファイル名 (カンマ区切り) から束縛先への対応で DI を組み立てる。

            DI.of(UnitOfWork, {"postgres": PostgresUnitOfWork}, InMemUnitOfWork())
        """
        return DI(
            interface,
            {Profile(set(actives.split(","))): a_class for actives, a_class in classes.items()},
            default,
        )

    def configure(self, binder: Binder) -> None:
        # interface は ABC を受けるため Callable で持つ (DIContainer.resolve と同じ理由)。
        binder.bind(self.interface, to=Switcher.get(self.classes, self.default), scope=singleton)  # type: ignore[arg-type]
