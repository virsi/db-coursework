"""Репозиторий оценок."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class GradesRepository(BaseRepository):
    table = "grades"
    columns = ("id", "student_id", "task_id", "score", "graded_at")

    @classmethod
    def listing(cls, query: str | None = None, *, student_id: int | None = None) -> list[dict]:
        sql = """
            SELECT g.id, g.student_id, g.task_id, g.score, g.graded_at,
                   s.full_name AS student_name,
                   t.title     AS task_title,
                   c.name      AS course_name
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN tasks    t ON t.id = g.task_id
            JOIN courses  c ON c.id = t.course_id
        """
        params: list = []
        conditions = []
        if student_id is not None:
            conditions.append("g.student_id = %s")
            params.append(student_id)
        if query:
            conditions.append("(s.full_name ILIKE %s OR t.title ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY g.graded_at DESC"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
