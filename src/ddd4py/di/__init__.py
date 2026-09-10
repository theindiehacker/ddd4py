"""DI コンテナ。injector の薄いラッパで、プロファイルによる実装差し替えを提供する。"""

from ddd4py.di.container import DIContainer
from ddd4py.di.di import DI

__all__ = ["DI", "DIContainer"]
