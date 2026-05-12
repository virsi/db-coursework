"""Главное меню студента (только просмотр)."""

from functools import partial

from app.views._menu_base import MenuView
from app.views.reports.score_100_view import Score100View
from app.views.reports.student_courses_view import StudentCoursesView
from app.views.reports.student_grades_view import StudentGradesView


class StudentMenuView(MenuView):
    title = "Меню студента"

    def items(self):
        sid = self.session.profile.get("id")
        return [
            ("Мои курсы",    partial(StudentCoursesView, student_id=sid)),
            ("Мои оценки",   partial(StudentGradesView,  student_id=sid)),
            ("100-балльная система", partial(Score100View, student_id=sid)),
        ]
