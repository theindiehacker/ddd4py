from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from injector import Injector

if TYPE_CHECKING:
    from collections.abc import Callable

    from ddd4py.di.di import DI

T = TypeVar("T")


class DIContainer:
    """プロセス全体で 1 つの injector を共有するコンテナ。"""

    __shared: DIContainer | None = None

    def __init__(self) -> None:
        self.__injector = Injector([])

    @classmethod
    def instance(cls) -> DIContainer:
        if cls.__shared is None:
            cls.__shared = DIContainer()
        return cls.__shared

    @classmethod
    def reset(cls) -> None:
        """共有インスタンスを破棄し、次の instance() に新しい injector を作らせる。

        injector の singleton スコープは束縛ごとにインスタンスをキャッシュするため、同じ
        interface を再 register しても**前に解決済みのインスタンスが生き残る**。テストが
        単体では通るのにまとめて走らせると落ちる典型がこれなので、テスト間で呼ぶ。

            @pytest.fixture(autouse=True)
            def _di() -> Iterator[None]:
                DIContainer.reset()
                DomainEventPublisher.instance().reset()
                yield
        """
        cls.__shared = None

    def register(self, *di: DI) -> None:
        # injector の束縛は後勝ち。後から register したものが前の束縛を差し替える。
        for e in di:
            self.__injector.binder.install(e)

    def resolve(self, interface: Callable[..., T]) -> T:
        # ABC を渡すのが DI の常用なので type[T] ではなく Callable[..., T] で受ける
        # (type[T] だと mypy の type-abstract が呼び出し側で必ず発火する)。
        return self.__injector.get(interface)  # type: ignore[arg-type]
