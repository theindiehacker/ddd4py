"""アーキテクチャ規約 (import-linter の合成規約) を配るモジュール。

規約そのものは `ddd4py.linter.architecture` にある。common と同じく再エクスポートはしない
(どのモジュールの規約なのかを設定ファイル上に残すため)。

    [tool.importlinter]
    root_packages = ["identity", "billing"]
    contract_types = [
        "hexagonal: ddd4py.linter.architecture.Hexagonal",
        "modular_monolithic: ddd4py.linter.architecture.ModularMonolithic",
    ]

import-linter 本体は extras で入れる: uv add --dev "ddd4py[linter]"
"""
