"""Репозиторий курсов."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class CoursesRepository(BaseRepository):
    table = "courses"
    columns = ("id", "name", "start_date", "end_date", "teacher_id", "discipline_id")

    SEARCH_COLUMNS = ("name",)

    @classmethod
    def search(cls, query: str | None) -> list[dict]:
        sql = """
            SELECT c.id, c.name, c.start_date, c.end_date,
                   c.teacher_id, c.discipline_id,
                   t.full_name AS teacher_name,
                   d.name      AS discipline_name
            FROM courses c
            JOIN teachers    t ON t.id = c.teacher_id
            JOIN disciplines d ON d.id = c.discipline_id
        """
        params: list = []
        if query:
            sql += " WHERE c.name ILIKE %s OR t.full_name ILIKE %s OR d.name ILIKE %s"
            params = [f"%{query}%"] * 3
        sql += " ORDER BY c.start_date DESC"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    @classmethod
    def options(cls) -> list[tuple[int, str]]:
        return [(r["id"], r["name"]) for r in cls.list()]

    @classmethod
    def for_teacher(cls, teacher_id: int) -> list[dict]:
        sql = """
            SELECT c.*, d.name AS discipline_name
            FROM courses c
            JOIN disciplines d ON d.id = c.discipline_id
            WHERE c.teacher_id = %s
            ORDER BY c.start_date DESC
        """
        with Database.cursor() as cur:
            cur.execute(sql, (teacher_id,))
            return [dict(row) for row in cur.fetchall()]

    @classmethod
    def for_student(cls, student_id: int) -> list[dict]:
        sql = """
            SELECT c.*, d.name AS discipline_name, t.full_name AS teacher_name
            FROM enrollments e
            JOIN courses     c ON c.id = e.course_id
            JOIN teachers    t ON t.id = c.teacher_id
            JOIN disciplines d ON d.id = c.discipline_id
            WHERE e.student_id = %s AND e.is_active
            ORDER BY c.start_date DESC
        """
        with Database.cursor() as cur:
            cur.execute(sql, (student_id,))
            return [dict(row) for row in cur.fetchall()]
