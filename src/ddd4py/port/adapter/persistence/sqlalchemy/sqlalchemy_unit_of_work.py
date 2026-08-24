from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, override

from sqlalchemy.orm import DeclarativeMeta, Session, scoped_session, sessionmaker

from ddd4py.application import UnitOfWork
from ddd4py.port.adapter.persistence.sqlalchemy.session_preparer import NullSessionPreparer, SessionPreparer

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy import Engine


class SQLAlchemyUnitOfWork(UnitOfWork[DeclarativeMeta]):
    """単一 Engine に固定された SQLAlchemy の UnitOfWork。

    複数 DB を実行時に引き分けたい場合は、本クラスのインスタンスを複数持ち、それらへ委譲する
    ルーティング UoW を利用側で用意する (どの軸で引き分けるかは利用側の業務判断のため、
    カーネルはルーティングを規定しない)。

    同一 Engine に対する scoped_session はプロセス内で本クラスのインスタンス 1 つに集約すること。
    別インスタンスにすると、同じ Engine に独立したセッション・トランザクションが並立し、片方の
    書き込みが `@transactional` の commit に乗らない。
    """

    def __init__(self, engine: Engine, session_preparer: SessionPreparer | None = None):
        self.__engine = engine
        self.__session_preparer = session_preparer or NullSessionPreparer()
        self.__scoped_session = scoped_session(sessionmaker(
            bind=engine,
            autocommit=False,
            expire_on_commit=True,
        ))

    @property
    def engine(self) -> Engine:
        """本 UoW が bind する Engine。テストの fixture が同じ DB に生 Session を張るのに使う。"""
        return self.__engine

    @contextmanager
    def query(self) -> Generator[Session]:
        """SELECT クエリ発行用のセッションを発行する。

        トランザクション管理対象ではないデータの取得にはこのメソッドを利用する。
        更新 / 新規作成 / 削除、およびそのためのデータ取得は self.session() を利用する。
        """
        session = Session(bind=self.__engine)
        try:
            # autobegin のトランザクションに乗り、close() の rollback で復帰するため、
            # プールされたコネクションに設定が漏れない。
            self.__session_preparer.prepare(session)
            yield session
        finally:
            session.close()

    def session(self) -> Session:
        """トランザクション管理をするためにスレッドローカルのセッションを発行する。"""
        return self.__scoped_session()

    @override
    def mark(self, instance: DeclarativeMeta) -> None:
        """UnitOfWork の追跡対象に追加する。

        SQLAlchemy は永続化対象を session が追跡するため、本実装では何もしない。
        """

    @override
    def persist(self, instance: DeclarativeMeta) -> None:
        self.session().add(instance)

    @override
    def delete(self, *instances: DeclarativeMeta) -> None:
        for instance in instances:
            self.session().delete(instance)

    @override
    def start(self) -> None:
        if self.session().in_transaction():
            # モジュールを跨いだトランザクション (ネストした境界) は最外のトランザクションに join する
            # (実行文脈は最外の start() が適用済み)。
            return
        self.session().begin()
        # begin() は遅延 BEGIN のため、prepare 内の execute が実際のトランザクションを開いて
        # 設定を内側に置き、commit / rollback で自動復帰する。
        self.__session_preparer.prepare(self.session())

    @override
    def flush(self) -> None:
        self.session().flush()

    @override
    def rollback(self) -> None:
        # commit / rollback はスレッドローカルの後始末に scoped_session.remove() が要る。
        # session() は Session を返し remove() を持たないため、ここは scoped_session を直接引く。
        try:
            self.__scoped_session.rollback()
        finally:
            # remove() が現セッションを close() してレジストリから破棄する。後続の close() は
            # 空セッションを生成して即 close するだけの無駄になるため呼ばない。
            self.__scoped_session.remove()

    @override
    def commit(self) -> None:
        try:
            self.__scoped_session.commit()
        finally:
            self.__scoped_session.remove()
