# 🧱 DDD for python

モジュラモノリス + ドメイン駆動設計のカーネル。**業務語彙をひとつも持たない**ことを設計制約にしている。

アーキテクチャ契約の検査は [clean-architecture](https://github.com/theindiehacker/clean-architecture) が担う。
このリポジトリは「import できるカーネル」だけを配る。

## 入っているもの

| 層 | 提供するもの |
|:--|:--|
| 合成 | `AppModule` / `CompositeModule` — モジュールの宣言点と合成ルート |
| 集約 | `DomainEvent` / `DomainEventPublisher` / `DomainEventSubscriber` / `DomainRegistry` |
| ユースケース | `UnitOfWork` / `ApplicationServiceLifeCycle` / `@transactional` |
| outbox | `StoredEvent` / `EventStore` / `EventContextProvider` |
| inbox | `ConsumedNotification` / `ConsumedNotificationStore` / `MessageSubscriber` |
| 発行 | `Notification` / `NotificationPublisher` / `PublishedNotificationTracker` |
| アダプタ | `InMem*`（テスト用） / `SQLAlchemyUnitOfWork`（extras: `sqlalchemy`） |
| 適合テスト | `ddd4py.testing.verify_*` — 自分のアダプタ実装が契約を満たすか検証する |

## 導入

```bash
uv add ddd4py
uv add "ddd4py[sqlalchemy]"   # SQLAlchemy アダプタも使う場合
```

## トランザクションと配送の保証

`@transactional` の内側で publish されたドメインイベントは、集約の更新と**同一トランザクション**で
outbox（`StoredEvent`）に追記される。ネストした境界は最外に join し、内側で失敗すれば最外まで巻き戻る
（部分 commit を許さない）。

受信側は `MessageSubscriber._dispatch` が listener ごとにトランザクションを開始し、
consumed marker の INSERT（claim-before-process）と listener の副作用を単一トランザクションで commit する
（Idempotent Consumer / transactional inbox）。at-least-once の重複は marker の unique 制約が先勝ち 1 つに絞る。

## 実行文脈というただ 1 つの拡張点

カーネルは「いま誰のリクエストを処理しているか」を知らない。知っているのは、outbox にそれを**刻印する**
ことと、受信時にそれを**確立する**ことだけ。

```python
from ddd4py import EventContext, EventContextProvider

class TenantContextProvider(EventContextProvider):
    def current(self) -> EventContext:
        tenant = CurrentTenant.get()
        return EventContext(partition_key=tenant.id, payload=tenant.to_dict())

    @contextmanager
    def bind(self, context: EventContext) -> Iterator[None]:
        with CurrentTenant.of(context.payload).bind():
            yield
```

単一テナントなら `NullEventContextProvider` のままでよい。

## 案件ごとの差し替え

`CompositeModule` は並べた順に DI を登録し、**後ろに置いたモジュールが前の束縛を差し替える**。
案件固有の実装は継承や上書きではなく、後ろにモジュールを足すことで注入する。

```python
CompositeModule([Core(), Authority(), Tenant(), AcmeOverrides()])
```

## 適合テスト

自分のアダプタ実装が契約を満たすかを、**利用側の CI で**検証する。

```python
from ddd4py.testing import verify_consumed_notification_store

def test_postgresql_consumed_notification_store(store):
    verify_consumed_notification_store(store)
```

## 開発

```bash
task init          # 依存インストール
task test          # テスト
task style:check   # ruff / mypy
task style:check:arch   # clean-architecture による自分自身への契約検査
```

## リリース

PyPI への公開は GitHub Release をトリガーに、[Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) で自動実行される。
API トークンはリポジトリに置かない。

```bash
# 1. pyproject.toml の version を上げて main へマージする
# 2. その version と同じタグで Release を作る (v プレフィックス付き)
gh release create v0.1.0 --generate-notes
```

タグと `pyproject.toml` の version が食い違うとワークフローは公開前に落ちる。
`__version__` は `pyproject.toml` から読むため、バージョンを書き換える箇所は `pyproject.toml` の 1 行だけ。

## ライセンス

MIT
