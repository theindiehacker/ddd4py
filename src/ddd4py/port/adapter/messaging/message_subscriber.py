from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

from di import DIContainer

from ddd4py.application import ApplicationServiceLifeCycle, EventContext
from ddd4py.event import EventContextProvider
from ddd4py.notification import ConsumedNotification, ConsumedNotificationStore

if TYPE_CHECKING:
    from ddd4py.port.adapter.messaging.exchange_listener import ExchangeListener

logger = logging.getLogger(__name__)


class MessageSubscriber(abc.ABC):
    """外部から送信されたメッセージを受信し、Listener に転送する。

    主に境界付けられたコンテキストから発生し、Pub/Sub・SNS・SQS などに送信されたドメインイベントを
    受信して Listener に転送する。
    """

    def __init__(self, consumer: str = "subscriber") -> None:
        # consumer は冪等性 inbox の dedup キーに含める consumer group 名。同一トピックを複数 group が
        # 購読しても互いの claim でスキップされないための次元。
        self.consumer = consumer
        self.listeners: set[ExchangeListener] = set()
        self.context: EventContext | None = None

    def add(self, listeners: set[ExchangeListener]) -> None:
        self.listeners = listeners

    def set_context(self, payload: dict | None, partition_key: str | None) -> None:
        if payload is None or partition_key is None:
            # 文脈の無い envelope は誤った境界で処理されるくらいなら fail-closed で弾く
            # (publisher は常に文脈を載せる前提。欠落は結線バグ)。
            raise ValueError("context is missing in the message; cannot resolve the execution context.")
        self.context = EventContext(partition_key, payload)

    @abc.abstractmethod
    async def receive(self, message: dict) -> None:
        pass

    async def _dispatch(self, publisher_name: str | None, event_type: str | None,
                        text_message: str, notification_id: int | None) -> None:
        """受信イベントの文脈を確立し、listener ごとの transactional inbox で転送する。

        1 envelope = 1 文脈。listener ごとにトランザクションを開始し、consumed marker の INSERT
        (claim-before-process) と listener の DB 副作用を単一トランザクションで commit する
        (Idempotent Consumer / transactional inbox)。途中でプロセスが落ちても marker と副作用は
        揃って巻き戻るため、再配送で漏れなく再処理される。at-least-once の重複 / 同時再配送は
        marker の unique 制約が先勝ち 1 つに絞る。listener 内の `@transactional` な
        ApplicationService はこのトランザクションに join する (ネスト深さ管理)。

        マルチ listener の部分失敗時は、成功 listener の marker が commit 済みのため再配送では
        失敗 listener だけが再実行される。失敗があっても全対象 listener を回し切ってから raise する
        (先頭の失敗で打ち切ると、set の順序不定により後続 listener が再配送のたびに飢え得るため)。
        メール送信などトランザクション外の副作用はこの保証の対象外で、従来どおり at-least-once。
        """
        if self.context is None:
            raise ValueError("context is not set. set_context() must be called before dispatch.")

        container = DIContainer.instance()
        provider: EventContextProvider = container.resolve(EventContextProvider)
        life_cycle: ApplicationServiceLifeCycle = container.resolve(ApplicationServiceLifeCycle)
        store: ConsumedNotificationStore = container.resolve(ConsumedNotificationStore)

        errors: list[Exception] = []
        with provider.bind(self.context):
            for listener in self.listeners:
                if not self.__listens(listener, publisher_name, event_type):
                    continue
                error = await self.__deliver(life_cycle, store, listener, event_type,
                                             text_message, notification_id)
                if error is not None:
                    errors.append(error)
        if errors:
            # nack して再配送させる (成功済み listener は marker で skip され再実行されない)
            raise errors[0]

    @staticmethod
    def __listens(listener: ExchangeListener, publisher_name: str | None, event_type: str | None) -> bool:
        return (listener.publisher_name() == publisher_name
                and event_type is not None
                and listener.listens_to(event_type))

    async def __deliver(self, life_cycle: ApplicationServiceLifeCycle, store: ConsumedNotificationStore,
                        listener: ExchangeListener, event_type: str, text_message: str,
                        notification_id: int | None) -> Exception | None:
        """1 listener 分の claim + 副作用を単一トランザクションで処理する。失敗時は例外を返す。"""
        # dedup キーの listener 次元は完全修飾名にする。単純クラス名だと別モジュールの同名 listener と
        # 衝突して片方が静かに skip される (リネーム時は既存 marker が orphan 化して再処理が走るが、
        # こちらは at-least-once の範囲で許容)。
        listener_name = f"{type(listener).__module__}.{type(listener).__qualname__}"
        life_cycle.begin()
        try:
            claim = ConsumedNotification(self.consumer, listener_name, notification_id, event_type)
            if notification_id is not None and not store.claim(claim):
                logger.info("notification %s は %s で処理済みのためスキップします", notification_id, listener_name)
                # 何も stage していないため rollback で破棄する (空 commit を残さない)
                life_cycle.fail()
                return None
            await listener.filtered_dispatch(event_type, text_message)
            life_cycle.success()
        except Exception as e:
            life_cycle.fail()
            logger.exception("listener %s の処理に失敗しました (notification %s)", listener_name, notification_id)
            return e
        return None
