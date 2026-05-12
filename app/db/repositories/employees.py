"""Репозиторий сотрудников (администраторов)."""

from app.db.connection import Database
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository


class EmployeesRepository(BaseRepository):
    table = "employees"
    columns = ("id", "user_id", "full_name", "position", "access_level")

    SEARCH_COLUMNS = ("full_name", "position", "access_level")

    ACCESS_LEVELS = (
        ("standard", "Стандартный"),
        ("extended", "Расширенный"),
        ("super",    "Полный"),
    )

    @classmethod
    def search(cls, query: str | None) -> list[dict]:
        return cls.list(search=query, search_columns=cls.SEARCH_COLUMNS) if query else cls.list()

    @classmethod
    def options(cls) -> list[tuple[int, str]]:
        return [(r["id"], r["full_name"]) for r in cls.list()]

    @classmethod
    def create_with_user(cls, *, login: str, password: str, full_name: str,
                         position: str, access_level: str = "standard") -> int:
        password_hash = UsersRepository.hash_password(password)
        with Database.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users (login, password_hash, role) "
                "VALUES (%s, %s, 'admin') RETURNING id",
                (login, password_hash),
            )
            user_id = cur.fetchone()["id"]
            cur.execute(
                "INSERT INTO employees (user_id, full_name, position, access_level) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, full_name, position, access_level),
            )
            return cur.fetchone()["id"]

    @classmethod
    def delete_with_user(cls, employee_id: int) -> None:
        with Database.cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM users WHERE id = "
                "(SELECT user_id FROM employees WHERE id = %s)",
                (employee_id,),
            )
