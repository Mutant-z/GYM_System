"""MySQL client placeholder.
MySQL 客户端占位文件。

This module will provide SQLAlchemy engine/session helpers and a basic
connectivity check for the gym business database.
这个模块后续会提供 SQLAlchemy 的引擎、会话工具，以及健身业务数据库的基础连通性检查。
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Iterator

from ..core import get_settings


class MySQLClient:
    """Lightweight MySQL access wrapper.
    轻量级 MySQL 访问封装。
    """

    def __init__(self, engine: Any, session_factory: Any) -> None:
        self._engine = engine
        self._session_factory = session_factory

    @property
    def engine(self) -> Any:
        """Return the SQLAlchemy engine.
        返回 SQLAlchemy 引擎。
        """

        return self._engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Provide a transactional session scope.
        提供事务型会话上下文。
        """

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ping(self) -> bool:
        """Check whether MySQL is reachable.
        检查 MySQL 是否可达。
        """

        try:
            from sqlalchemy import text
        except ImportError as exc:
            raise RuntimeError("SQLAlchemy is required for MySQL requests") from exc

        with self.session() as session:
            session.execute(text("SELECT 1"))
        return True


@lru_cache(maxsize=1)
def get_mysql_client() -> MySQLClient:
    """Build and cache a MySQL client from application settings.
    根据应用配置构建并缓存 MySQL 客户端。
    """

    settings = get_settings()
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
    except ImportError as exc:
        raise RuntimeError("SQLAlchemy is required for MySQL requests") from exc

    engine = create_engine(
        settings.mysql_sqlalchemy_url,
        connect_args={"connect_timeout": 3},
        pool_size=settings.mysql_pool_size,
        max_overflow=settings.mysql_max_overflow,
        pool_timeout=settings.mysql_pool_timeout_seconds,
        pool_recycle=settings.mysql_pool_recycle_seconds,
        echo=settings.mysql_echo,
        pool_pre_ping=True,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return MySQLClient(engine=engine, session_factory=session_factory)
