"""Отчёт «Средний балл по курсу»."""

from app.services.reports import average_score_per_course
from app.views.reports._base_report import ReportView


class AveragePerCourseView(ReportView):
    title = "Отчёт: средний балл по курсу"
    columns = (
        ("course_name",      "Курс"),
        ("discipline_name",  "Дисциплина"),
        ("teacher_name",     "Преподаватель"),
        ("grades_count",     "Количество оценок"),
        ("avg_score",        "Средний балл"),
    )

    def description(self) -> str:
        return ("Средний балл по каждому курсу: вычисляется как AVG(score) "
                "по всем оценкам всех студентов курса.")

    def fetch(self):
        return average_score_per_course()
