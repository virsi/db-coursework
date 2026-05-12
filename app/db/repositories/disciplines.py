"""Репозиторий учебных дисциплин."""

from app.db.repositories.base import BaseRepository


class DisciplinesRepository(BaseRepository):
    table = "disciplines"
    columns = ("id", "name", "hours", "description")

    SEARCH_COLUMNS = ("name", "description")

    @classmethod
    def search(cls, query: str | None) -> list[dict]:
        return cls.list(search=query, search_columns=cls.SEARCH_COLUMNS) if query else cls.list()

    @classmethod
    def options(cls) -> list[tuple[int, str]]:
        return [(r["id"], r["name"]) for r in cls.list()]
