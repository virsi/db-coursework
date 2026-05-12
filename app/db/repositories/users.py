"""Учётные записи и аутентификация."""

import bcrypt

from app.db.connection import Database
from app.db.repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    table = "users"
    columns = ("id", "login", "role", "created_at")
    pk = "id"

    @classmethod
    def find_by_login(cls, login: str) -> dict | None:
        sql = "SELECT id, login, password_hash, role FROM users WHERE login = %s"
        with Database.cursor() as cur:
            cur.execute(sql, (login,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(10)).decode("utf-8")

    @classmethod
    def linked_profile(cls, user_id: int, role: str) -> dict | None:
        """Профиль пользователя в зависимости от роли."""
        table = {"admin": "employees", "teacher": "teachers", "student": "students"}.get(role)
        if not table:
            return None
        with Database.cursor() as cur:
            cur.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
