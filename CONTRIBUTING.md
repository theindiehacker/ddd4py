# Development

## Set up
```bash
task init          # 依存インストール
task test          # テスト
task style:check   # ruff format / ruff / mypy / import-linter (自分自身への契約検査)
task style:fix     # 整形 + lint の自動修正
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

## CI

PR には以下のチェックが走る。

| ワークフロー | 検知するもの |
|:---|:---|
| `ci.yml` | 整形 (ruff format) / lint (ruff) / 型 (mypy) / テスト / アーキテクチャ規約 (import-linter) |
| org の必須ワークフロー | シークレット混入 (Gitleaks) / SAST (Semgrep) / 依存パッケージの脆弱性・IaC の設定ミス (Trivy) / GitHub Actions 定義 (zizmor / ghalint / actionlint) など |

org の必須ワークフローは [theindiehacker/github-workflows](https://github.com/theindiehacker/github-workflows) の定義を org ルールセットで全リポジトリに適用しているため、本リポジトリには置かない。

### `ci.yml` を必須にする (リポジトリ管理者向け)

ワークフローを置いただけではマージはブロックされない。
Settings → Rules → Rulesets → New branch ruleset で、
**Target branches** を `Include default branch`、
**Require status checks to pass** に `検査` を登録する。

> チェック名は job 名がそのまま出たもの。
> job 名を変えると必須チェックの名前も変わり、PR が永久に pending になるため変更しない。

### 検知の抑制

誤検知の抑制は、org ルールセット「セキュリティ設定変更の承認必須化」の対象である
設定ファイル (`.gitleaksignore` / `.trivyignore` / `.semgrepignore` / `.github/zizmor.yml`) に限定する。
各ツールのインライン抑制コメント (gitleaks の allow / Semgrep の nosem /
Trivy と zizmor の ignore) は承認ゲートを迂回するため、
各ワークフローで明示的に無効化、または存在自体を禁止している。

> ここでトークンを原文のまま書いていないのは、Trivy ワークフローの禁止チェックが
> リポジトリ全体を grep するため、この文書自身が検知されてしまうため。

これらの設定ファイルは**検出が実際に出て、誤検知だと判断できた時にだけ**作る。
先回りして空ファイルを置かないこと。特に `.semgrepignore` は、存在するだけで
Semgrep の組み込み既定除外リストを置き換えてしまう。
