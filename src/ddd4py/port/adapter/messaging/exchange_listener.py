from __future__ import annotations

import abc


class ExchangeListener(abc.ABC):
    """他モジュールが発行したドメインイベントを購読する入力アダプタ。"""

    @abc.abstractmethod
    async def filtered_dispatch(self, event_type: str, text_message: str) -> None:
        """イベントタイプとメッセージ指定でメッセージを処理する"""

    @abc.abstractmethod
    def publisher_name(self) -> str:
        """購読するイベント発行元コンテキスト名を指定する"""

    @abc.abstractmethod
    def listens_to(self, event_type: str) -> bool:
        """イベントタイプ指定で購読するイベントかどうかを判定する"""
