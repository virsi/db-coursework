"""Универсальный виджет отчёта: таблица + кнопки печати/обновления."""

from typing import Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.reports.printer import print_table


class ReportView(QWidget):
    title: str = ""
    columns: Sequence[tuple[str, str]] = ()  # (поле_строки, заголовок)
    width: int = 920
    height: int = 520

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"АС ОУДО — {self.title}")
        self.resize(self.width, self.height)
        self._rows: list[dict] = []
        self._build()
        self.refresh()

    def fetch(self) -> list[dict]:
        raise NotImplementedError

    def description(self) -> str:
        return ""

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel(self.title)
        font = header.font()
        font.setPointSize(14)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        if self.description():
            note = QLabel(self.description())
            note.setStyleSheet("color: #555;")
            note.setWordWrap(True)
            layout.addWidget(note)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.columns])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)
        print_btn = QPushButton("Печать")
        print_btn.setProperty("role", "secondary")
        print_btn.clicked.connect(self._on_print)
        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("role", "secondary")
        close_btn.clicked.connect(self.close)
        buttons.addWidget(refresh_btn)
        buttons.addWidget(print_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def refresh(self) -> None:
        try:
            self._rows = self.fetch()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))
            return
        self.table.setRowCount(len(self._rows))
        for r, row in enumerate(self._rows):
            for c, (field, _) in enumerate(self.columns):
                value = row.get(field)
                self.table.setItem(r, c, QTableWidgetItem("" if value is None else str(value)))

    def _on_print(self) -> None:
        print_table(self, self.title,
                    [c[1] for c in self.columns],
                    [c[0] for c in self.columns],
                    self._rows)
