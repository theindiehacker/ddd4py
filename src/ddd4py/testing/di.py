from __future__ import annotations

from di import DIContainer

from ddd4py.domain.model import DomainEventPublisher

# DIContainer のシングルトン参照 (name mangling 後の属性名)。
_SHARED_ATTR = "_DIContainer__shared"


def reset_di_container() -> None:
    """DI コンテナとドメインイベント購読者を破棄し、次のテストへ状態を持ち越さない。

    injector の singleton スコープは束縛ごとにインスタンスをキャッシュするため、同じ interface を
    再 register しても**前のテストで解決済みのインスタンスが生き残る**。テストが単体では通るのに
    まとめて走らせると落ちる典型がこれなので、テストキットとして配る。

        @pytest.fixture(autouse=True)
        def _di() -> Iterator[None]:
            reset_di_container()
            yield
            reset_di_container()
    """
    # di4injector 0.0.2 はリセット API を持たないため、シングルトン参照を直接落とす。
    # setattr は存在しない名前でも黙って通るため、先に存在を確認する。確認しないと
    # di4injector の内部実装が変わった瞬間にリセットが無言で効かなくなり、テストが
    # 「単体では通るのにまとめると落ちる」状態へ静かに戻る (この関数が防いでいる当のもの)。
    if not hasattr(DIContainer, _SHARED_ATTR):
        raise RuntimeError(
            f"di4injector の内部実装が変わりました ({DIContainer.__module__}.{_SHARED_ATTR} が無い)。"
            " reset_di_container の実装を追随させてください。",
        )
    setattr(DIContainer, _SHARED_ATTR, None)
    DomainEventPublisher.instance().reset()
