"""モジュラモノリス + DDD のカーネルを配るディストリビューション。

配布するモジュールは `ddd4py.<module>` に置く (現在は `ddd4py.common` のみ)。
このパッケージ自身は API を持たず、バージョンだけを公開する。
"""

from importlib.metadata import version

# バージョンの真実源は pyproject.toml の [project].version 一箇所。
# 引数は import 名ではなく配布名 (どちらも ddd4py)。
__version__ = version("ddd4py")

__all__ = ["__version__"]
