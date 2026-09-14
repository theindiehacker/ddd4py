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

PR には以下のチェックが走る。すべて `.github/workflows/` にワークフローの実体がある
(以前は org 共通リポジトリの必須ワークフローとして外部から注入されていた)。

| ワークフロー | 検知するもの |
|:---|:---|
| `ci.yml` | 整形 (ruff format) / lint (ruff) / 型 (mypy) / テスト / アーキテクチャ規約 (import-linter) |
| `gitleaks.yml` | PR 差分へのシークレット混入 |
| `semgrep.yml` | アプリケーションコードの脆弱性 (SAST) |
| `trivy.yml` | 依存パッケージ (`uv.lock`) の脆弱性 / IaC の設定ミス |
| `zizmor.yml` | GitHub Actions 定義の脆弱性 |
| `ghalint.yml` | GitHub Actions 定義のセキュリティポリシー違反 |
| `actionlint.yml` | GitHub Actions 定義の構文 (`run:` 内のシェルを含む) |

### 検知を必須にする (リポジトリ管理者向け)

ワークフローを置いただけではマージはブロックされない。
Settings → Rules → Rulesets → New branch ruleset で、
**Target branches** を `Include default branch`、
**Require status checks to pass** に以下のチェック名を登録する。

```
検査
シークレット検知
アプリケーションコードをスキャン
依存パッケージ / IaC をスキャン
GitHub Actions 設定をスキャン
workflow セキュリティポリシーチェック
workflow 構文チェック
```

> チェック名は各ワークフローの **job 名** がそのまま出たもの。
> job 名を変えると必須チェックの名前も変わり、PR が永久に pending になるため変更しない。

あわせて org 管理者側で:

- 必須ワークフローを使う org ルールセット (シークレットの混入検知 / 脆弱性・IaC 設定ミス検知 /
  スタイルチェック) の **Target repositories からこのリポジトリを外す**。
  実体が private リポジトリにあるため public の本 repo では実行されず、状態が曖昧になる。
- 「検知ワークフロー変更の承認必須化」ルールセットの **Target repositories に本 repo を追加する**。
  このルールは org 共通リポジトリのみを対象にしているため、移設した検知ワークフロー
  (`.github/workflows/`) はセキュリティチームの承認なしに弱められてしまう。

### 検知の抑制

誤検知の抑制は、org ルールセット「セキュリティ設定変更の承認必須化」の対象である
設定ファイル (`.gitleaksignore` / `.trivyignore` / `.semgrepignore` / `.github/zizmor.yml`) に限定する。
各ツールのインライン抑制コメント (gitleaks の allow / Semgrep の nosem /
Trivy と zizmor の ignore) は承認ゲートを迂回するため、
各ワークフローで明示的に無効化、または存在自体を禁止している。

> ここでトークンを原文のまま書いていないのは、`trivy.yml` の禁止チェックが
> リポジトリ全体を grep するため、この文書自身が検知されてしまうため。

これらの設定ファイルは**検出が実際に出て、誤検知だと判断できた時にだけ**作る。
先回りして空ファイルを置かないこと。特に `.semgrepignore` は、存在するだけで
Semgrep の組み込み既定除外リストを置き換えてしまう。
