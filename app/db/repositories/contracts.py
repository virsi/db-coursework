"""Репозиторий договоров."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class ContractsRepository(BaseRepository):
    table = "contracts"
    columns = ("id", "employee_id", "student_id", "teacher_id",
               "contract_type", "contract_date", "is_active")

    TYPES = (
        ("education",  "Об обучении"),
        ("employment", "Трудовой"),
    )

    @classmethod
    def listing(cls, query: str | None = None) -> list[dict]:
        sql = """
            SELECT c.id, c.contract_type, c.contract_date, c.is_active,
                   c.employee_id, c.student_id, c.teacher_id,
                   e.full_name AS employee_name,
                   s.full_name AS student_name,
                   t.full_name AS teacher_name
            FROM contracts c
            JOIN employees e ON e.id = c.employee_id
            LEFT JOIN students s ON s.id = c.student_id
            LEFT JOIN teachers t ON t.id = c.teacher_id
        """
        params: list = []
        if query:
            sql += (" WHERE e.full_name ILIKE %s OR s.full_name ILIKE %s "
                    "OR t.full_name ILIKE %s")
            params = [f"%{query}%"] * 3
        sql += " ORDER BY c.contract_date DESC"
        with Database.cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
