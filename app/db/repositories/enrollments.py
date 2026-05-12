"""Репозиторий записей студентов на курсы."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class EnrollmentsRepository(BaseRepository):
    table = "enrollments"
    columns = ("id", "student_id", "course_id", "enrollment_date", "is_active")

    @classmethod
    def listing(cls, query: str | None = None) -> list[dict]:
        sql = """
            SELECT e.id, e.student_id, e.course_id, e.enrollment_date, e.is_active,
                   s.full_name AS student_name,
                   c.name      AS course_name
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            JOIN courses  c ON c.id = e.course_id
        """
        params: list = []
        if query:
            sql += " WHERE s.full_name ILIKE %s OR c.name ILIKE %s"
            params = [f"%{query}%"] * 2
        sql += " ORDER BY e.enrollment_date DESC"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
