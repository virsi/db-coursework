"""Окно авторизации."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from app.services.auth import AuthError, Session, login


class LoginView(QWidget):
    authenticated = pyqtSignal(object)  # испускает Session при успешном входе

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("АС ОУДО — Авторизация")
        self.setMinimumWidth(380)
        from app.views._menu_base import _disable_native_fullscreen
        _disable_native_fullscreen(self)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("Вход в систему")
        title.setAlignment(Qt.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        subtitle = QLabel(
            "АС ОУДО — Автоматизированная система\n"
            "образовательного учреждения дистанционного обучения"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #555;")
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("admin / teacher1 / student1")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_submit)
        form.addRow("Логин:", self.login_input)
        form.addRow("Пароль:", self.password_input)
        layout.addLayout(form)

        self.submit_btn = QPushButton("Войти")
        self.submit_btn.setDefault(True)
        self.submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(self.submit_btn)

        self.exit_btn = QPushButton("Выйти из приложения")
        self.exit_btn.setProperty("role", "secondary")
        self.exit_btn.clicked.connect(self.close)
        layout.addWidget(self.exit_btn)

    def _on_submit(self) -> None:
        login_text = self.login_input.text().strip()
        password = self.password_input.text()
        if not login_text or not password:
            QMessageBox.warning(self, "Внимание", "Введите логин и пароль.")
            return
        try:
            session = login(login_text, password)
        except AuthError as exc:
            QMessageBox.critical(self, "Ошибка авторизации", str(exc))
            self.password_input.clear()
            return
        self.authenticated.emit(session)
        self.close()
