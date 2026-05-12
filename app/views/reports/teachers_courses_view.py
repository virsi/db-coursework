"""Отчёт «Преподаватели и курсы»."""

from app.services.reports import teachers_with_courses
from app.views.reports._base_report import ReportView


class TeachersCoursesView(ReportView):
    title = "Отчёт: преподаватели и их курсы"
    columns = (
        ("teacher_name",   "Преподаватель"),
        ("position",       "Должность"),
        ("specialization", "Специализация"),
        ("courses_count",  "Количество курсов"),
        ("courses",        "Курсы"),
    )

    def description(self) -> str:
        return "Список преподавателей с привязанными к ним курсами."

    def fetch(self):
        return teachers_with_courses()
