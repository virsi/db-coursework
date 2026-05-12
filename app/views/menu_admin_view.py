"""Главное меню администратора (Сотрудника)."""

from app.views._menu_base import MenuView
from app.views.crud.contracts_view import ContractsView
from app.views.crud.courses_view import CoursesView
from app.views.crud.disciplines_view import DisciplinesView
from app.views.crud.employees_view import EmployeesView
from app.views.crud.enrollments_view import EnrollmentsView
from app.views.crud.students_view import StudentsView
from app.views.crud.teachers_view import TeachersView
from app.views.reports.charts_view import ChartsReportView
from app.views.reports.course_overview_view import CourseOverviewView
from app.views.reports.enrollment_summary_view import EnrollmentSummaryView
from app.views.reports.teachers_courses_view import TeachersCoursesView


class AdminMenuView(MenuView):
    title = "Меню сотрудника"

    def items(self):
        return [
            ("Студенты",         StudentsView),
            ("Преподаватели",    TeachersView),
            ("Сотрудники",       EmployeesView),
            ("Дисциплины",       DisciplinesView),
            ("Курсы",            CoursesView),
            ("Запись на курс",   EnrollmentsView),
            ("Договоры",         ContractsView),
            ("Отчёт: курсы",     CourseOverviewView),
            ("Отчёт: запись",    EnrollmentSummaryView),
            ("Отчёт: преподаватели", TeachersCoursesView),
            ("Аналитика (графики)", ChartsReportView),
        ]
