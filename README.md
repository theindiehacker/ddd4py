# 🧱 DDD for python

モジュラモノリス + ドメイン駆動設計のカーネル。**業務語彙をひとつも持たない**ことを設計制約にしている。

「import できるカーネル」と、それを守るための[import-linter](https://github.com/seddonym/import-linter) 規約を配る。

## How To
### ⬇️ Install

```bash
uv add ddd4py
uv add "ddd4py[sqlalchemy]"   # SQLAlchemy アダプタも使う場合
```

### 🛠️ Use

<details><summary><b>📦 DI コンテナ</b></summary>

登録方法:
```python
from sqlalchemy import create_engine

from ddd4py.common.application import UnitOfWork
from ddd4py.common.port.adapter.persistence.inmem import InMemUnitOfWork
from ddd4py.common.port.adapter.persistence.sqlalchemy import SQLAlchemyUnitOfWork
from ddd4py.di import DI, DIContainer

engine = create_engine("postgresql+psycopg://...")

DIContainer.instance().register(
    DI.of(UnitOfWork, {"InMem": InMemUnitOfWork()}, SQLAlchemyUnitOfWork(engine)),
)
```

利用方法:
```python
from ddd4py.di import DI, DIContainer

# `DI_FOR_PY=InMem` なら InMemUnitOfWork のインタンスを取得
# `DI_FOR_PY=` なら SQLAlchemyUnitOfWork のインタンスを取得
unit_of_work = DIContainer.instance().resolve(UnitOfWork)
```

```python
from injector import inject

class 〇〇ApplicationService:
    @inject
    def __init__(self, 〇〇_repository: 〇〇Repository) -> None:
        ...
```

```python
from ddd4py.common.domain.model import DomainRegistry

〇〇_repository = DomainRegistry.resolve(〇〇Repository)
```

</details>