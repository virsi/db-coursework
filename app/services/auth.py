"""Сервис аутентификации."""

from dataclasses import dataclass

from app.db.repositories.users import UsersRepository


@dataclass(frozen=True)
class Session:
    user_id: int
    login: str
    role: str
    profile: dict           # employees / teachers / students row
    full_name: str


class AuthError(Exception):
    """Ошибка авторизации (неверный логин или пароль)."""


def login(login_text: str, password: str) -> Session:
    user = UsersRepository.find_by_login(login_text.strip())
    if user is None or not UsersRepository.verify_password(password, user["password_hash"]):
        raise AuthError("Неверный логин или пароль")

    profile = UsersRepository.linked_profile(user["id"], user["role"]) or {}
    return Session(
        user_id=user["id"],
        login=user["login"],
        role=user["role"],
        profile=profile,
        full_name=profile.get("full_name", user["login"]),
    )
