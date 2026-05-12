"""Репозиторий заданий."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class TasksRepository(BaseRepository):
    table = "tasks"
    columns = ("id", "course_id", "title", "description", "type", "deadline", "max_score")

    TYPES = (
        ("homework",   "Домашнее задание"),
        ("lab",        "Лабораторная работа"),
        ("test",       "Тест"),
        ("control",    "Контрольная работа"),
        ("essay",      "Эссе"),
        ("coursework", "Курсовая работа"),
        ("exam",       "Экзамен"),
    )

    @classmethod
    def listing(cls, query: str | None = None, *, course_id: int | None = None) -> list[dict]:
        sql = """
            SELECT t.id, t.title, t.description, t.type, t.deadline, t.max_score,
                   t.course_id, c.name AS course_name
            FROM tasks t
            JOIN courses c ON c.id = t.course_id
        """
        params: list = []
        conditions = []
        if course_id is not None:
            conditions.append("t.course_id = %s")
            params.append(course_id)
        if query:
            conditions.append("(t.title ILIKE %s OR c.name ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY t.deadline DESC"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    @classmethod
    def options_for_course(cls, course_id: int) -> list[tuple[int, str]]:
        with Database.cursor() as cur:
            cur.execute(
                "SELECT id, title FROM tasks WHERE course_id = %s ORDER BY deadline",
                (course_id,),
            )
            return [(r["id"], r["title"]) for r in cur.fetchall()]
