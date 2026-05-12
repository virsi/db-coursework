"""Отчёт «100-балльная система»."""

from app.services.reports import score_100_system
from app.views.reports._base_report import ReportView


class Score100View(ReportView):
    title = "Отчёт: 100-балльная система"
    columns = (
        ("student_name",    "Студент"),
        ("course_name",     "Курс"),
        ("score_100",       "Итог (100-балльная)"),
        ("weighted_score",  "Взвешенная сумма"),
        ("total_weight",    "Сумма весов"),
    )

    def __init__(self, student_id: int | None = None) -> None:
        self.student_id = student_id
        super().__init__()

    def description(self) -> str:
        return ("Итоговая 100-балльная оценка по курсам с учётом весов заданий: "
                "homework/lab — 0.5, test/control — 1.0, essay/coursework — 1.5, exam — 2.0.")

    def fetch(self):
        return score_100_system(self.student_id)
