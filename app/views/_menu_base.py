"""Базовый класс главных меню по ролям."""

import sys
from collections.abc import Callable

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QGridLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from app.services.auth import Session


def _disable_native_fullscreen(widget: QWidget) -> None:
    """На macOS «зелёная кнопка» по умолчанию переводит окно в native
    fullscreen (отдельный Space). Дочерние окна тогда открываются в
    основном Space, а исходное Space остаётся видимым после их
    закрытия — пользователь видит чёрный экран до перезапуска.
    Подавляем native fullscreen-кнопку, оставляя обычный maximize.
    """
    if sys.platform == "darwin":
        widget.setWindowFlag(Qt.WindowFullscreenButtonHint, False)


class MenuView(QWidget):
    """Заголовок + сетка кнопок + кнопки «Выйти из аккаунта/приложения»."""

    logout_requested = pyqtSignal()

    title: str = ""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session
        self.setWindowTitle(f"АС ОУДО — {self.title}")
        self.setMinimumSize(640, 420)
        self._open_children: list[QWidget] = []
        _disable_native_fullscreen(self)
        self._build()

    def items(self) -> list[tuple[str, Callable[[], QWidget]]]:
        """Подклассы возвращают список (надпись_кнопки, фабрика_окна)."""
        raise NotImplementedError

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        header = QLabel(self.title)
        header.setAlignment(Qt.AlignCenter)
        font = header.font()
        font.setPointSize(18)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)

        greeting = QLabel(f"Здравствуйте, {self.session.full_name}!")
        greeting.setAlignment(Qt.AlignCenter)
        greeting.setStyleSheet("color: #555;")
        layout.addWidget(greeting)

        grid = QGridLayout()
        grid.setSpacing(12)
        for index, (label, factory) in enumerate(self.items()):
            row, col = divmod(index, 3)
            btn = QPushButton(label)
            btn.setMinimumHeight(60)
            btn.clicked.connect(self._make_handler(factory))
            grid.addWidget(btn, row, col)
        layout.addLayout(grid)

        layout.addStretch(1)

        logout_btn = QPushButton("Выйти из аккаунта")
        logout_btn.setProperty("role", "secondary")
        logout_btn.clicked.connect(self._on_logout)
        layout.addWidget(logout_btn)

        exit_btn = QPushButton("Выйти из приложения")
        exit_btn.setProperty("role", "danger")
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

    def _make_handler(self, factory: Callable[[], QWidget]):
        def handler() -> None:
            try:
                widget = factory()
            except Exception as exc:  # на показ — окно с ошибкой
                QMessageBox.critical(self, "Ошибка", str(exc))
                return
            # Делаем дочернее окно модальным к меню. На macOS это
            # удерживает его в том же Space, что и развёрнутое главное
            # окно, а при закрытии Qt автоматически возвращает фокус —
            # не остаётся чёрного экрана.
            widget.setParent(self, Qt.Window)
            widget.setWindowModality(Qt.WindowModal)
            widget.setAttribute(Qt.WA_DeleteOnClose, True)
            _disable_native_fullscreen(widget)
            widget.show()
            widget.raise_()
            widget.activateWindow()
            self._open_children.append(widget)
        return handler

    def _on_logout(self) -> None:
        # Дочерние окна могли уже самоуничтожиться (WA_DeleteOnClose);
        # закрытие deleted-объекта бросает RuntimeError — глушим.
        for w in list(self._open_children):
            try:
                w.close()
            except RuntimeError:
                pass
        self._open_children.clear()
        self.logout_requested.emit()
