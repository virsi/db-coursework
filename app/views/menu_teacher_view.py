"""Главное меню преподавателя."""

from app.views._menu_base import MenuView
from app.views.crud.grades_view import GradesView
from app.views.crud.tasks_view import TasksView
from app.views.crud.variants_view import VariantsView
from app.views.reports.average_per_course_view import AveragePerCourseView
from app.views.reports.charts_view import ChartsReportView
from app.views.reports.score_100_view import Score100View
from app.views.reports.student_grades_view import StudentGradesView


class TeacherMenuView(MenuView):
    title = "Меню преподавателя"

    def items(self):
        return [
            ("Задания",            TasksView),
            ("Варианты",           VariantsView),
            ("Оценки",             GradesView),
            ("100-балльная система", Score100View),
            ("Средний балл",       AveragePerCourseView),
            ("Баллы студента",     StudentGradesView),
            ("Аналитика (графики)", ChartsReportView),
        ]
