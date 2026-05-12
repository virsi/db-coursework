"""Отчёт «Сводка по записи студентов»."""

from app.services.reports import enrollment_summary
from app.views.reports._base_report import ReportView


class EnrollmentSummaryView(ReportView):
    title = "Отчёт: сводка по записи студентов"
    columns = (
        ("student_name",          "Студент"),
        ("student_status",        "Статус"),
        ("active_enrollments",    "Активных записей"),
        ("inactive_enrollments",  "Неактивных"),
        ("first_enrollment",      "Первая запись"),
        ("last_enrollment",       "Последняя запись"),
    )

    def description(self) -> str:
        return ("Агрегированная статистика записи каждого студента на курсы "
                "и хронология его учебной деятельности.")

    def fetch(self):
        return enrollment_summary()
