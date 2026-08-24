from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventContext:
    """StoredEvent / Notification に刻印される実行文脈。

    カーネルは「文脈が何であるか」を知らない。知っているのは 2 つだけ:

    - `partition_key`: subscriber がイベントを処理する境界を解決するためのキー。
      マルチテナントなら App / テナントの識別子、単一テナントなら既定値のまま。
    - `payload`: 受信側が文脈を復元するのに必要な全情報 (JSON 化可能なこと)。

    利用側は自分の語彙 (App / Pool / Organization など) をこの 2 値に翻訳して渡す。
    カーネルに業務語彙を持ち込まないための境界がここ。
    """

    DEFAULT_PARTITION_KEY = "default"

    partition_key: str = DEFAULT_PARTITION_KEY
    payload: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.partition_key:
            raise ValueError("partition_key must not be empty")
