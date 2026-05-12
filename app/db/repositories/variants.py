"""Репозиторий вариантов заданий."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class VariantsRepository(BaseRepository):
    table = "variants"
    columns = ("id", "task_id", "number", "description")

    @classmethod
    def listing(cls, query: str | None = None) -> list[dict]:
        sql = """
            SELECT v.id, v.task_id, v.number, v.description,
                   t.title AS task_title
            FROM variants v
            JOIN tasks t ON t.id = v.task_id
        """
        params: list = []
        if query:
            sql += " WHERE t.title ILIKE %s OR v.description ILIKE %s"
            params = [f"%{query}%"] * 2
        sql += " ORDER BY t.title, v.number"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
