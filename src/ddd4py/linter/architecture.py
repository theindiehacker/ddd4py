import abc
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, override

from importlinter import Contract, ContractCheck, output
from importlinter.contracts.independence import IndependenceContract
from importlinter.contracts.layers import LayersContract
from importlinter.contracts.protected import ProtectedContract

if TYPE_CHECKING:
    from grimp import ImportGraph


class ArchitectureContract(Contract):
    """複数の規約を束ね、1 つの規約として検査・描画する合成規約"""

    @property
    @abc.abstractmethod
    def contracts(self) -> list[Contract]:
        """束ねる規約"""

    @override
    def check(self, graph: ImportGraph, verbose: bool) -> ContractCheck:
        # 各規約はグラフを書き換える (ignore_imports の除去など) ため、複製を渡して互いに干渉させない
        results: list[tuple[Contract, ContractCheck]] = [
            (contract, contract.check(deepcopy(graph), verbose)) for contract in self.contracts
        ]

        return ContractCheck(
            kept=all(check.kept for _, check in results),
            metadata={"results": results},
            warnings=[warning for _, check in results for warning in check.warnings],
            ignored_import_count=sum(check.ignored_import_count for _, check in results),
        )

    @override
    def render_broken_contract(self, check: ContractCheck) -> None:
        results: list[tuple[Contract, ContractCheck]] = check.metadata["results"]
        for contract, result in results:
            if result.kept:
                continue
            # 内訳の規約は自身の名前を描画しないため、どの規約が破れたのかをここで見出しとして出す
            output.print_heading(contract.name, output.HEADING_LEVEL_THREE, style=output.ERROR)
            contract.render_broken_contract(result)


class Hexagonal(ArchitectureContract):
    """ヘキサゴナルアーキテクチャ(モジュール内部に関する規約)"""
    type_name = "architecture.hexagonal"

    @property
    @override
    def contracts(self) -> list[Contract]:
        return [
            LayersContract(
                name="ヘキサゴナルアーキテクチャの依存違反を禁止",
                session_options=self.session_options,
                contract_options={
                    # (x) = optional / そのモジュールに無くてよい
                    # a : b = 同一層・相互 import 可能
                    "layers": [
                        "core",
                        "(middleware)",
                        "port",
                        "application",
                        "domain",
                        "exception",
                    ],
                    "containers": self.session_options["root_packages"],
                    "exhaustive": "false",  # layers で定義したモジュール以外は違反チェックしない
                },
            ),
            # 上の layers 規約だけでは、ポートアダプター層から直接ドメイン層をインポートできるため、プロテクト規約を定義
            ProtectedContract(
                name="ドメイン層の依存違反を禁止",
                session_options=self.session_options,
                contract_options={
                    "protected_modules": ["*.domain"],
                    "allowed_importers": [
                        "*.core",
                        "*.application",
                        "*.port.adapter.persistence",
                        "*.port.adapter.service",
                    ],
                },
            ),
        ]


class ModularMonolithic(ArchitectureContract):
    """モジュラモノリスアーキテクチャ(モジュール境界に関する規約)"""
    type_name = "architecture.modularmonolithic"

    class RootPackagesContract(Contract):
        type_name = "architecture.root"

        MODULE_DIRECTORY = Path("backend/src")

        @override
        def check(self, graph: ImportGraph, verbose: bool) -> ContractCheck:
            directory = self.MODULE_DIRECTORY
            if not directory.is_dir():
                raise ValueError(
                    f"{directory} が見つからない。モジュールは {directory} 直下に置き、"
                    f"lint-imports はその親 (リポジトリルート) から実行する。",
                )
            packages = {path.name for path in directory.iterdir() if (path / "__init__.py").is_file()}
            unregistered = sorted(packages - set(self.session_options["root_packages"]))
            return ContractCheck(
                kept=not unregistered,
                metadata={"unregistered": unregistered, "directory": directory},
            )

        @override
        def render_broken_contract(self, check: ContractCheck) -> None:
            for name in check.metadata["unregistered"]:
                path = check.metadata["directory"] / name
                output.print_error(f"- {path} が root_packages に未登録 (追記すれば全規約が自動で適用される)",
                                   bold=False)
            output.new_line()

    @property
    @override
    def contracts(self) -> list[Contract]:
        return [
            self.RootPackagesContract(
                name="backend/src にあるモジュールがすべて root_packages に登録されているか検査",
                session_options=self.session_options,
                contract_options={},
            ),
            IndependenceContract(
                name="モジュール間の連携は腐敗防止層 (ACL アダプター) から公開 IF (port.adapter.resource) へのみ",
                session_options=self.session_options,
                contract_options={
                    "modules": self.session_options["root_packages"],
                    "ignore_imports": ["*.port.adapter.service.*.adapter.** -> *.port.adapter.resource.**"],
                    # モジュールが1つしかない場合、モジュール間連携が行われずエラーになるので "none" を指定
                    "unmatched_ignore_imports_alerting": "none",
                },
            ),
        ]
