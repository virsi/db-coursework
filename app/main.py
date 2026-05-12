"""Точка входа приложения АС ОУДО."""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from app.db.connection import Database, check_connection
from app.services.auth import Session
from app.styles import apply_theme
from app.views.login_view import LoginView
from app.views.menu_admin_view import AdminMenuView
from app.views.menu_student_view import StudentMenuView
from app.views.menu_teacher_view import TeacherMenuView


def open_menu_for(session: Session) -> None:
    """Открыть главное меню для указанной роли."""
    if session.role == "admin":
        window = AdminMenuView(session)
    elif session.role == "teacher":
        window = TeacherMenuView(session)
    else:
        window = StudentMenuView(session)
    window.logout_requested.connect(_on_logout)
    window.show()
    _OPEN_WINDOWS.append(window)


_OPEN_WINDOWS: list = []


def _on_logout() -> None:
    """Закрыть текущие окна и снова показать форму авторизации."""
    for w in list(_OPEN_WINDOWS):
        w.close()
    _OPEN_WINDOWS.clear()
    _show_login()


def _show_login() -> None:
    login_window = LoginView()
    login_window.authenticated.connect(open_menu_for)
    login_window.show()
    _OPEN_WINDOWS.append(login_window)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("АС ОУДО")
    app.setOrganizationName("МГТУ им. Н. Э. Баумана")
    apply_theme(app)

    Database.init()
    ok, info = check_connection()
    if not ok:
        QMessageBox.critical(
            None, "Ошибка подключения",
            "Не удалось подключиться к базе данных PostgreSQL.\n\n" + info,
        )
        return 1

    _show_login()
    exit_code = app.exec_()
    Database.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
