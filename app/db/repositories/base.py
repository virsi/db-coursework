"""Базовый репозиторий с общими CRUD-операциями."""

from typing import Any, Iterable

from app.db.connection import Database


class BaseRepository:
    """Универсальный репозиторий поверх одной таблицы.

    Конкретные репозитории задают только имя таблицы и список колонок,
    а сложные запросы (JOIN, агрегаты) пишутся в наследниках вручную.
    """

    table: str = ""
    columns: tuple[str, ...] = ()
    pk: str = "id"

    @classmethod
    def list(cls, *, search: str | None = None, search_columns: Iterable[str] = ()) -> list[dict]:
        sql = f"SELECT * FROM {cls.table}"
        params: list[Any] = []
        if search and search_columns:
            conditions = " OR ".join(f"{c}::text ILIKE %s" for c in search_columns)
            sql += f" WHERE {conditions}"
            params.extend([f"%{search}%"] * len(tuple(search_columns)))
        sql += f" ORDER BY {cls.pk}"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    @classmethod
    def get(cls, pk: int) -> dict | None:
        with Database.cursor() as cur:
            cur.execute(f"SELECT * FROM {cls.table} WHERE {cls.pk} = %s", (pk,))
            row = cur.fetchone()
            return dict(row) if row else None

    @classmethod
    def create(cls, **values: Any) -> int:
        cols = list(values.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        sql = (
            f"INSERT INTO {cls.table} ({', '.join(cols)}) "
            f"VALUES ({placeholders}) RETURNING {cls.pk}"
        )
        with Database.cursor(commit=True) as cur:
            cur.execute(sql, list(values.values()))
            return cur.fetchone()[cls.pk]

    @classmethod
    def update(cls, pk: int, **values: Any) -> None:
        if not values:
            return
        assignments = ", ".join(f"{c} = %s" for c in values)
        sql = f"UPDATE {cls.table} SET {assignments} WHERE {cls.pk} = %s"
        with Database.cursor(commit=True) as cur:
            cur.execute(sql, [*values.values(), pk])

    @classmethod
    def delete(cls, pk: int) -> None:
        with Database.cursor(commit=True) as cur:
            cur.execute(f"DELETE FROM {cls.table} WHERE {cls.pk} = %s", (pk,))
