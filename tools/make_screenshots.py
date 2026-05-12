"""Генерация реальных скриншотов UI АС ОУДО.

Подход: рендерим каждый виджет в pixmap через QWidget.grab() с
выставленным атрибутом Qt.WA_DontShowOnScreen. Окна не появляются на
экране, никакого взаимодействия с пользователем не требуется.

Запуск:
    .venv/bin/python tools/make_screenshots.py

Требования:
    - поднят PostgreSQL (make db-up && make db-init);
    - установлены зависимости из requirements.txt.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtCore import QDate, QDateTime, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "screenshots"


# -------------------------------------------------------------------- helpers --
def grab(widget: QWidget, name: str, *, w: int = 1200, h: int = 760) -> None:
    """Сохранить скриншот виджета без показа на экране."""
    widget.setAttribute(Qt.WA_DontShowOnScreen, True)
    widget.resize(w, h)
    widget.show()
    for _ in range(3):
        QApplication.processEvents()
    target = OUT / f"{name}.png"
    widget.grab().save(str(target))
    widget.close()
    widget.deleteLater()
    print(f"  ✓ {target.relative_to(ROOT)}")


def grab_messagebox(icon, title: str, text: str, name: str,
                    buttons=QMessageBox.Ok) -> None:
    mb = QMessageBox()
    mb.setIcon(icon)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setStandardButtons(buttons)
    mb.setAttribute(Qt.WA_DontShowOnScreen, True)
    mb.show()
    for _ in range(3):
        QApplication.processEvents()
    mb.grab().save(str(OUT / f"{name}.png"))
    mb.close()
    print(f"  ✓ docs/screenshots/{name}.png")


def session_from_profile(role: str, profile_id: int) -> "Session":
    """Создать Session для нужной роли на основе данных из БД."""
    from app.db.repositories.users import UsersRepository
    from app.services.auth import Session

    table_map = {"admin": "employees", "teacher": "teachers", "student": "students"}
    table = table_map[role]
    from app.db.connection import Database
    with Database.cursor() as cur:
        cur.execute(f"SELECT * FROM {table} WHERE id = %s", (profile_id,))
        profile = dict(cur.fetchone())
    return Session(
        user_id=profile["user_id"],
        login=f"{role}{profile_id}" if role != "admin" else "admin",
        role=role,
        profile=profile,
        full_name=profile["full_name"],
    )


# -------------------------------------------------------------------- main ----
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setApplicationName("АС ОУДО")

    from app.styles import apply_theme
    apply_theme(app)

    from app.db.connection import Database
    Database.init()
    print("PostgreSQL подключение установлено.")

    # Импортируем UI-модули после создания QApplication.
    from app.views.crud.contracts_view import ContractsView
    from app.views.crud.courses_view import CoursesView
    from app.views.crud.disciplines_view import DisciplinesView
    from app.views.crud.employees_view import EmployeesView
    from app.views.crud.enrollments_view import EnrollmentsView
    from app.views.crud.grades_view import GradesView
    from app.views.crud.students_view import StudentsView
    from app.views.crud.tasks_view import TasksView
    from app.views.crud.teachers_view import TeachersView
    from app.views.crud.variants_view import VariantsView
    from app.views.login_view import LoginView
    from app.views.menu_admin_view import AdminMenuView
    from app.views.menu_student_view import StudentMenuView
    from app.views.menu_teacher_view import TeacherMenuView
    from app.views.reports.average_per_course_view import AveragePerCourseView
    from app.views.reports.course_overview_view import CourseOverviewView
    from app.views.reports.enrollment_summary_view import EnrollmentSummaryView
    from app.views.reports.score_100_view import Score100View
    from app.views.reports.student_courses_view import StudentCoursesView
    from app.views.reports.student_grades_view import StudentGradesView
    from app.views.reports.teachers_courses_view import TeachersCoursesView

    print("Снимаю формы аутентификации и меню…")
    # 01 — окно авторизации с введёнными данными
    lv = LoginView()
    lv.login_input.setText("admin")
    lv.password_input.setText("admin")
    grab(lv, "01_login", w=520, h=460)

    # 02 — сообщение об ошибке авторизации
    grab_messagebox(QMessageBox.Critical, "Ошибка авторизации",
                    "Неверный логин или пароль", "02_login_error")

    # Меню
    admin_session   = session_from_profile("admin", 1)
    teacher_session = session_from_profile("teacher", 1)
    student_session = session_from_profile("student", 1)

    grab(AdminMenuView(admin_session),     "03_menu_admin",   w=920, h=680)
    grab(TeacherMenuView(teacher_session), "04_menu_teacher", w=920, h=560)
    grab(StudentMenuView(student_session), "05_menu_student", w=720, h=420)

    # CRUD-формы
    print("Снимаю CRUD-формы…")
    grab(StudentsView(),    "10_students_list")

    sv_add = StudentsView()
    sv_add.login_input.setText("test_student")
    sv_add.password_input.setText("test_pwd_123")
    sv_add.full_name_input.setText("Тестовский Тест Тестович")
    sv_add.enrollment_input.setDate(QDate(2025, 9, 1))
    grab(sv_add, "11_students_add")

    sv_search = StudentsView()
    sv_search.search_input.setText("Воробьёв")
    sv_search.refresh()
    grab(sv_search, "12_students_search")

    grab(TeachersView(),    "13_teachers")
    grab(EmployeesView(),   "14_employees")
    grab(DisciplinesView(), "15_disciplines")
    # Форма «Курсы» с выделенной первой строкой — демонстрация master-detail:
    # подчинённая таблица «Задания курса» наполняется автоматически.
    cv = CoursesView()
    if cv._rows:
        cv.table.selectRow(0)
    grab(cv, "16_courses", w=1200, h=820)
    grab(EnrollmentsView(), "17_enrollments")
    grab(ContractsView(),   "18_contracts")
    grab(TasksView(),       "19_tasks")
    grab(VariantsView(),    "20_variants")
    grab(GradesView(),      "21_grades")

    # Отчёты
    print("Снимаю отчёты…")
    grab(CourseOverviewView(),     "30_report_courses")
    grab(EnrollmentSummaryView(),  "31_report_enrollments")
    grab(TeachersCoursesView(),    "32_report_teachers")
    grab(AveragePerCourseView(),   "33_report_avg_course")
    grab(Score100View(),           "34_report_100")
    grab(StudentGradesView(),      "35_report_student_grades")
    grab(StudentCoursesView(student_id=student_session.profile["id"]),
                                   "36_report_student_courses", w=1000, h=520)

    # Окно предпросмотра печати — статическое HTML через QTextDocument
    print("Снимаю предпросмотр печати…")
    from PyQt5.QtGui import QPageLayout, QTextDocument
    from PyQt5.QtPrintSupport import QPrintPreviewWidget, QPrinter
    from app.reports.printer import _html_table, _html_card

    rows = [{"course_name": f"Курс {i}", "discipline_name": "Математика",
             "teacher_name": "Иванов И.И.", "active_students": 12}
            for i in range(1, 6)]
    doc = QTextDocument()
    doc.setHtml(_html_table("Список курсов",
                            ["Курс", "Дисциплина", "Преподаватель", "Студентов"],
                            ["course_name", "discipline_name", "teacher_name",
                             "active_students"], rows))
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageOrientation(QPageLayout.Landscape)
    preview = QPrintPreviewWidget(printer)
    preview.paintRequested.connect(doc.print_)
    grab(preview, "40_print_preview", w=1100, h=720)

    # Графические отчёты Qt Charts: столбчатая и круговая диаграммы.
    # Анимация при offscreen-рендеринге не успевает завершиться —
    # выключаем её, чтобы столбики/сектора отрисовались сразу.
    print("Снимаю графические отчёты…")
    from PyQt5.QtChart import QChart
    from app.views.reports.charts_view import ChartsReportView
    charts = ChartsReportView()
    for view in (charts.bar_view, charts.pie_view):
        c = view.chart()
        if c is not None:
            c.setAnimationOptions(QChart.NoAnimation)
    charts.tabs.setCurrentIndex(0)
    grab(charts, "41_charts_report", w=1100, h=760)

    charts2 = ChartsReportView()
    for view in (charts2.bar_view, charts2.pie_view):
        c = view.chart()
        if c is not None:
            c.setAnimationOptions(QChart.NoAnimation)
    charts2.tabs.setCurrentIndex(1)
    grab(charts2, "41b_charts_pie", w=1100, h=760)

    # Карточка студента — печатный шаблон одной сущности.
    print("Снимаю карточку студента…")
    from app.services.reports import student_grades
    sid = 1
    grades = student_grades(sid)
    detail_rows = [
        (g.get("course_name") or "", g.get("task_title") or "",
         str(g.get("task_type") or ""),
         f"{g.get('score', 0)}/{g.get('max_score', 100)}",
         (g.get("graded_at").strftime("%d.%m.%Y")
          if hasattr(g.get("graded_at"), "strftime") else "—"))
        for g in grades[:8]
    ]
    avg = (f"{sum(g['score'] for g in grades) / len(grades):.2f}"
           if grades else "—")
    card_doc = QTextDocument()
    card_doc.setHtml(_html_card(
        title="Карточка студента",
        header="Воробьёв Егор Александрович",
        rows=[
            ("Идентификатор",   "1"),
            ("ФИО",             "Воробьёв Егор Александрович"),
            ("Статус обучения", "Учится"),
            ("Дата зачисления", "01.09.2024"),
            ("Всего оценок",    str(len(grades))),
            ("Средний балл",    avg),
        ],
        detail_title=f"Оценки студента ({len(grades)} записей)",
        detail_headers=("Курс", "Задание", "Тип", "Балл", "Дата"),
        detail_rows=detail_rows,
    ))
    card_printer = QPrinter(QPrinter.HighResolution)
    card_printer.setPageOrientation(QPageLayout.Portrait)
    card_preview = QPrintPreviewWidget(card_printer)
    card_preview.paintRequested.connect(card_doc.print_)
    grab(card_preview, "42_student_card", w=900, h=900)

    # Системные сообщения
    print("Снимаю системные диалоги…")
    grab_messagebox(QMessageBox.Information, "Готово", "Запись добавлена.",
                    "50_msg_added")
    grab_messagebox(QMessageBox.Warning, "Проверка",
                    "Поле «ФИО» обязательно для заполнения.",
                    "51_msg_validation")
    grab_messagebox(QMessageBox.Question, "Подтверждение",
                    "Удалить запись №42?", "52_msg_delete_confirm",
                    buttons=QMessageBox.Yes | QMessageBox.No)
    grab_messagebox(QMessageBox.Critical, "Ошибка подключения",
                    "Не удалось подключиться к базе данных PostgreSQL.\n\n"
                    "could not connect to server: Connection refused\n"
                    "    Is the server running on host \"localhost\" and "
                    "accepting TCP/IP connections on port 5433?",
                    "60_db_connect_error")

    Database.close()
    print(f"\nГотово. Скриншоты сохранены в {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
