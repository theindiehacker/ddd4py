"""ポート実装の適合テスト (contract test) キット。

フレームワークが「このポートはこう振る舞うこと」を実行可能な形で配り、**利用側プロジェクトの CI で**
自分のアダプタ実装に対して走らせる。カーネルを上げたときに自分の実装が契約から外れていないか、
また案件ごとに差し替えた実装が同じ契約を満たすかを、利用側で検出するための安全装置。

pytest の継承基底ではなく素の関数として配るのは、利用側のテスト規約 (継承基底の禁止) を壊さず、
テストの呼び出し関係をコード上で追えるようにするため。

    def test_postgresql_consumed_notification_store(store):
        verify_consumed_notification_store(store)
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from ddd4py.notification import ConsumedNotification, PublishedNotificationTracker

if TYPE_CHECKING:
    from collections.abc import Callable

    from ddd4py.application import UnitOfWork
    from ddd4py.domain.model import DomainEvent
    from ddd4py.event import EventStore
    from ddd4py.notification import ConsumedNotificationStore, PublishedNotificationTrackerStore


def verify_unit_of_work(unit_of_work: UnitOfWork) -> None:
    """UnitOfWork の契約。

    - start → commit / start → rollback が例外なく完了する
    - start の二重呼び出し (ネストした境界) が例外にならない ... 最外の境界に join するため
    - commit / rollback 後に再度 start できる ... 1 プロセスで複数リクエストを捌くため
    """
    unit_of_work.start()
    unit_of_work.flush()
    unit_of_work.commit()

    unit_of_work.start()
    unit_of_work.rollback()

    unit_of_work.start()
    unit_of_work.start()  # ネストした境界は join し、例外にしない
    unit_of_work.commit()


def verify_event_store(event_store: EventStore, domain_event_factory: Callable[[], DomainEvent]) -> None:
    """EventStore (outbox) の契約。

    - append したイベントが all_stored_events_since(0) で取得できる
    - event_id は追記順に単調増加する ... 未発行分を「直近発行 ID より大きいもの」で引くため
    - since は排他的 (指定 ID 自身を含まない) ... 同じ通知を二重発行しないため
    """
    before = len(event_store.all_stored_events_since(0))

    event_store.append(domain_event_factory())
    event_store.append(domain_event_factory())

    stored = event_store.all_stored_events_since(0)
    assert len(stored) == before + 2, f"append した 2 件が取得できていません: {len(stored)} 件"

    ids = [e.event_id for e in stored]
    assert ids == sorted(ids), f"event_id が追記順に単調増加していません: {ids}"
    assert all(e.partition_key for e in stored), "partition_key が刻印されていません"

    since_first = event_store.all_stored_events_since(ids[0])
    assert ids[0] not in [e.event_id for e in since_first], "since は排他的でなければなりません"


def verify_consumed_notification_store(store: ConsumedNotificationStore) -> None:
    """ConsumedNotificationStore (inbox) の契約。

    - 同一キーの 2 回目の claim は False ... at-least-once の再配送を二重処理しないため
    - listener が違えば別 claim ... マルチ listener の部分失敗時に成功分だけ skip するため
    - consumer が違えば別 claim ... 複数 consumer group が独立に処理できるため
    - prune は削除件数を返す
    """
    base = ConsumedNotification("subscriber", "acme.FooListener", 1, "UserProvisioned.1")

    assert store.claim(base) is True, "初回の claim は True でなければなりません"
    assert store.claim(base) is False, "同一キーの再 claim は False でなければなりません (重複排除)"

    other_listener = ConsumedNotification(base.consumer, "acme.BarListener", base.notification_id, base.event_type)
    assert store.claim(other_listener) is True, "listener が違えば独立に claim できなければなりません"

    other_consumer = ConsumedNotification("worker", base.listener, base.notification_id, base.event_type)
    assert store.claim(other_consumer) is True, "consumer が違えば独立に claim できなければなりません"

    assert isinstance(store.prune(timedelta(days=30)), int), "prune は削除件数 (int) を返さなければなりません"


def verify_published_notification_tracker_store(store: PublishedNotificationTrackerStore) -> None:
    """PublishedNotificationTrackerStore の契約。

    - 未登録の発行先を引くと新規トラッカーが返る ... 初回起動時に発行が止まらないため
    - track した値が次の取得で読める
    - 発行先ごとに独立している ... 同じ通知列を複数トピックへ別タイミングで発行できるため
    """
    tracker = store.published_notification_tracker_of("notifications")
    assert isinstance(tracker, PublishedNotificationTracker), "未登録でも新規トラッカーを返さなければなりません"

    tracker.most_recent_published_notification_id = 42
    store.track_most_recent_published_notification(tracker)

    reloaded = store.published_notification_tracker_of("notifications")
    assert reloaded.most_recent_published_notification_id == 42, "track した発行 ID が読み戻せません"

    other = store.published_notification_tracker_of("audit-log")
    assert other.most_recent_published_notification_id == 0, "発行先ごとに独立していなければなりません"
