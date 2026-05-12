"""Репозиторий студентов."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository


class StudentsRepository(BaseRepository):
    table = "students"
    columns = ("id", "user_id", "full_name", "enrollment_date", "status")

    SEARCH_COLUMNS = ("full_name", "status")

    STATUSES = (
        ("studying",       "Учится"),
        ("academic_leave", "Академический отпуск"),
        ("expelled",       "Отчислен"),
        ("graduated",      "Окончил"),
    )

    @classmethod
    def search(cls, query: str | None) -> list[dict]:
        return cls.list(search=query, search_columns=cls.SEARCH_COLUMNS) if query else cls.list()

    @classmethod
    def create_with_user(cls, *, login: str, password: str, full_name: str,
                         enrollment_date, status: str = "studying") -> int:
        password_hash = UsersRepository.hash_password(password)
        with Database.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users (login, password_hash, role) "
                "VALUES (%s, %s, 'student') RETURNING id",
                (login, password_hash),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO students (user_id, full_name, enrollment_date, status) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, full_name, enrollment_date, status),
            )
            return cur.fetchone()["id"]

    @classmethod
    def delete_with_user(cls, student_id: int) -> None:
        with Database.cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM users WHERE id = "
                "(SELECT user_id FROM students WHERE id = %s)",
                (student_id,),
            )
