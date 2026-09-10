# Development

## Set up
```bash
task init          # 依存インストール
task test          # テスト
task style:check   # ruff / mypy / import-linter (自分自身への契約検査)
```

## Debug

ローカルの変更を、実際のリポジトリに撃って確かめる手順。

```bash
cd path/to/対象プロジェクト
uv add --dev --editable path/to/ddd4py   # 一度だけ
```

## Release

PyPI への公開は GitHub Release をトリガーに、[Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) で自動実行される。
API トークンはリポジトリに置かない。

```bash
# 1. pyproject.toml の version を上げて main へマージする
# 2. その version と同じタグで Release を作る (v プレフィックス付き)
gh release create v0.1.0 --generate-notes
```

タグと `pyproject.toml` の version が食い違うとワークフローは公開前に落ちる。
`__version__` は `pyproject.toml` から読むため、バージョンを書き換える箇所は `pyproject.toml` の 1 行だけ。
