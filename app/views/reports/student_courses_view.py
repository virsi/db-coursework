"""Отчёт «Мои курсы» для студента."""

from app.db.repositories.courses import CoursesRepository
from app.views.reports._base_report import ReportView


class StudentCoursesView(ReportView):
    title = "Мои курсы"
    columns = (
        ("name",             "Курс"),
        ("discipline_name",  "Дисциплина"),
        ("teacher_name",     "Преподаватель"),
        ("start_date",       "Начало"),
        ("end_date",         "Окончание"),
    )

    def __init__(self, student_id: int | None = None) -> None:
        self.student_id = student_id
        super().__init__()

    def description(self) -> str:
        return "Курсы, на которые вы записаны и которые сейчас активны."

    def fetch(self):
        if self.student_id is None:
            return []
        return CoursesRepository.for_student(self.student_id)
