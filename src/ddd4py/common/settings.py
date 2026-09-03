from __future__ import annotations

from typing import Any, ClassVar, Self

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """全設定クラスの共通基底。

    各サブクラスは `instance()` でシングルトンとして取得できる。
    """

    model_config = SettingsConfigDict(env_file=None, extra="ignore", populate_by_name=True)

    _instance: ClassVar[Any] = None

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """シングルトンを破棄する (環境変数を差し替えるテストで使う)。"""
        cls._instance = None


class CoreSettings(BaseAppSettings):
    """カーネルが読む最小限の設定。業務設定は利用側が BaseAppSettings を継承して定義する。"""

    di_profile_actives: str = Field(default="", validation_alias="DI_PROFILE_ACTIVES")
    notification_publish_to: str = Field(default="notifications", validation_alias="NOTIFICATION_PUBLISH_TO")

    @property
    def profiles(self) -> set[str]:
        """DI_PROFILE_ACTIVES をカンマ区切りの set に変換する"""
        return {p.strip() for p in self.di_profile_actives.split(",") if p.strip()}
