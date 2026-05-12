"""Отчёт «Список курсов»."""

from app.services.reports import course_overview
from app.views.reports._base_report import ReportView


class CourseOverviewView(ReportView):
    title = "Отчёт: список курсов"
    columns = (
        ("course_name",      "Курс"),
        ("discipline_name",  "Дисциплина"),
        ("hours",            "Часы"),
        ("teacher_name",     "Преподаватель"),
        ("teacher_position", "Должность"),
        ("start_date",       "Начало"),
        ("end_date",         "Окончание"),
        ("active_students",  "Студентов"),
    )

    def description(self) -> str:
        return ("Каталог всех курсов системы с информацией о ведущем преподавателе, "
                "дисциплине, часах и количестве активно записанных студентов.")

    def fetch(self):
        return course_overview()
