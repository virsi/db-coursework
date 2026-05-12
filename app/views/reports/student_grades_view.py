"""Отчёт «Баллы студента»."""

from app.services.reports import student_grades
from app.views.reports._base_report import ReportView


class StudentGradesView(ReportView):
    title = "Отчёт: баллы студента"
    columns = (
        ("student_name",     "Студент"),
        ("course_name",      "Курс"),
        ("discipline_name",  "Дисциплина"),
        ("task_title",       "Задание"),
        ("task_type",        "Тип"),
        ("score",            "Балл"),
        ("max_score",        "Макс."),
        ("graded_at",        "Дата"),
    )

    def __init__(self, student_id: int | None = None) -> None:
        self.student_id = student_id
        super().__init__()

    def description(self) -> str:
        if self.student_id:
            return "Все оценки выбранного студента по всем курсам."
        return "Все оценки всех студентов (для администрации и преподавателей)."

    def fetch(self):
        return student_grades(self.student_id)
