"""Репозиторий преподавателей."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository


class TeachersRepository(BaseRepository):
    table = "teachers"
    columns = ("id", "user_id", "full_name", "position", "specialization")

    SEARCH_COLUMNS = ("full_name", "position", "specialization")

    @classmethod
    def search(cls, query: str | None) -> list[dict]:
        return cls.list(search=query, search_columns=cls.SEARCH_COLUMNS) if query else cls.list()

    @classmethod
    def options(cls) -> list[tuple[int, str]]:
        return [(r["id"], r["full_name"]) for r in cls.list()]

    @classmethod
    def create_with_user(cls, *, login: str, password: str, full_name: str,
                         position: str, specialization: str) -> int:
        password_hash = UsersRepository.hash_password(password)
        with Database.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users (login, password_hash, role) "
                "VALUES (%s, %s, 'teacher') RETURNING id",
                (login, password_hash),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO teachers (user_id, full_name, position, specialization) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, full_name, position, specialization),
            )
            return cur.fetchone()["id"]

    @classmethod
    def delete_with_user(cls, teacher_id: int) -> None:
        with Database.cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM users WHERE id = "
                "(SELECT user_id FROM teachers WHERE id = %s)",
                (teacher_id,),
            )
