"""Пул соединений и контекст-менеджеры для работы с PostgreSQL."""

from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from app.config import DBConfig, load_db_config


class Database:
    """Тонкая обёртка над пулом psycopg2."""

    _pool: SimpleConnectionPool | None = None
    _config: DBConfig | None = None

    @classmethod
    def init(cls, config: DBConfig | None = None, *, minconn: int = 1, maxconn: int = 5) -> None:
        cls._config = config or load_db_config()
        cls._pool = SimpleConnectionPool(minconn, maxconn, dsn=cls._config.dsn)

    @classmethod
    def close(cls) -> None:
        if cls._pool is not None:
            cls._pool.closeall()
            cls._pool = None

    @classmethod
    @contextmanager
    def connection(cls) -> Iterator[PgConnection]:
        if cls._pool is None:
            cls.init()
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def cursor(cls, *, commit: bool = False) -> Iterator[RealDictCursor]:
        with cls.connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cur
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()


def check_connection() -> tuple[bool, str]:
    """Возвращает (успех, сообщение). Используется на старте приложения."""
    try:
        with Database.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()["version"]
        return True, version
    except psycopg2.Error as exc:
        return False, str(exc)
