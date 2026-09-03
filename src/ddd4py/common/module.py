from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from ddd4py.common.port.adapter.messaging import ExchangeListener


class AppModule:
    """モジュラモノリスの 1 モジュール。DI 設定・購読者・テーブル定義の宣言点。

    全メソッドが既定実装 (何もしない) を持つ。モジュールは必要なものだけを override する
    (DI 登録だけのモジュール / 購読だけのモジュールがあるため、抽象メソッドにしない)。

    トランスポート (FastAPI 等) には依存しない。ルーティングを公開したいモジュールは、
    利用側プロジェクトで本クラスを継承した基底に `router` プロパティを足す。
    """

    class Launch(StrEnum):
        API = "api"
        SUBSCRIBER = "subscriber"
        BATCH = "batch"
        TEST = "test"

    async def startup(self) -> None:
        """アプリ起動前に実行すべき処理 (DI 登録など) を定義する"""

    async def shutdown(self) -> None:
        """アプリ終了時に実行すべき処理を定義する"""

    @property
    def listeners(self) -> set[ExchangeListener]:
        """本モジュールが購読する ExchangeListener を定義する"""
        return set()

    @property
    def tables(self) -> list[str]:
        """マイグレーション自動検出用のドライバーモジュールパスを定義する。

        テーブルクラスを持つモジュールはオーバーライドすること。
        """
        return []


class CompositeModule(AppModule):
    """複数の AppModule を 1 つに束ねる合成ルート。

    ここに並べた順序が DI 登録の順序になる。injector の束縛は後勝ちのため、
    **後ろに置いたモジュールが前のモジュールの束縛を差し替えられる**。案件ごとの実装差し替えは
    フレームワーク側モジュールの後ろに自前モジュールを足すことで実現する (継承・上書き不要)。

        CompositeModule([Core(), Authority(), Tenant(), AcmeOverrides()])
    """

    def __init__(self, modules: list[AppModule]):
        self.__modules = modules

    @property
    def modules(self) -> list[AppModule]:
        return list(self.__modules)

    @override
    async def startup(self) -> None:
        for module in self.__modules:
            await module.startup()

    @override
    async def shutdown(self) -> None:
        for module in reversed(self.__modules):
            await module.shutdown()

    @override
    @property
    def listeners(self) -> set[ExchangeListener]:
        return {listener for module in self.__modules for listener in module.listeners}

    @override
    @property
    def tables(self) -> list[str]:
        return [table for module in self.__modules for table in module.tables]
