from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime

    from ddd4py.common.domain.model import DomainEvent, EventContext

# `<発行元モジュール>.<ドメインイベントのクラス名>.<イベントバージョン>`
# 各部は Python 識別子 (unicode 可)。"." で 3 分割できることが不変条件なので、区切り文字と
# 空白の混入だけを弾く。ユビキタス言語をそのままクラス名にする言語 (日本語等) を排除しない。
_TYPE_PATTERN = re.compile(r"[^\W\d]\w*\.[^\W\d]\w*\.\d+")


@dataclass(init=True, frozen=True)
class StoredEvent:
    """トランザクショナル outbox の 1 行。集約の更新と同一トランザクションで永続化される。"""

    event_id: int | None
    type: str
    event_body: dict
    occurred_on: datetime.datetime
    # イベントを処理すべき境界のキー (既定は発生元)。subscriber がこのキーで処理文脈を解決するため、
    # イベントは処理先を自己記述する。境界をまたぐイベントは routing_context() の申告値で上書きされる。
    partition_key: str
    context: dict

    def __post_init__(self) -> None:
        # fullmatch で全体一致を要求し、末尾改行・余剰文字の混入を弾く。
        if _TYPE_PATTERN.fullmatch(self.type) is None:
            raise ValueError(
                f"Invalid event type: '{self.type}'. "
                "Expected format: '<publisher>.<DomainEventClassName>.<version>'.",
            )
        if not self.partition_key:
            raise ValueError("partition_key must not be empty")

    @property
    def publisher(self) -> str:
        return self.type.split(".")[0]

    @property
    def event_type(self) -> str:
        """`{ドメインイベントのクラス名}.{イベントバージョン番号}` を返す"""
        return ".".join(self.type.split(".")[1:])

    @property
    def version(self) -> int:
        return int(self.type.split(".")[2])

    @staticmethod
    def new(event_id: int | None, domain_event: DomainEvent, context: EventContext) -> StoredEvent:
        return StoredEvent(
            event_id,
            f"{domain_event.__module__.split('.')[0]}.{domain_event.type}",
            domain_event.to_dict(),
            domain_event.occurred_on,
            context.partition_key,
            context.payload,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StoredEvent):
            return False
        if self.event_id is None or other.event_id is None:
            return False
        return self.event_id == other.event_id

    def __hash__(self) -> int:
        # 採番前 (event_id is None) でも set / dict に入れられること。
        return hash(("StoredEvent", self.event_id))
