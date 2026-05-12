"""Универсальный CRUD-виджет для табличных форм АС ОУДО."""

from typing import Any, Sequence

import psycopg2
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class CrudView(QWidget):
    """Базовая CRUD-форма: таблица + панель ввода + кнопки."""

    title: str = ""
    columns: Sequence[tuple[str, str]] = ()  # (поле строки, заголовок колонки)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"АС ОУДО — {self.title}")
        self.resize(960, 560)
        self._rows: list[dict] = []
        self._build()
        self.refresh()

    # --------------------------------------------------------------- UI ----
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        header = QLabel(self.title)
        font = header.font()
        font.setPointSize(14)
        font.setBold(True)
        header.setFont(font)
        outer.addWidget(header)

        # Поиск
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по таблице…")
        self.search_input.returnPressed.connect(self.refresh)
        search_btn = QPushButton("Найти")
        search_btn.clicked.connect(self.refresh)
        reset_btn = QPushButton("Сброс")
        reset_btn.setProperty("role", "secondary")
        reset_btn.clicked.connect(self._on_reset_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(search_btn)
        search_row.addWidget(reset_btn)
        outer.addLayout(search_row)

        # Таблица + форма
        splitter = QSplitter(Qt.Horizontal)
        outer.addWidget(splitter, 1)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.columns])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self._on_select)
        splitter.addWidget(self.table)

        form_panel = QWidget()
        self.form_layout = QVBoxLayout(form_panel)
        self.form_layout.setContentsMargins(8, 0, 0, 0)
        self.form_layout.setSpacing(8)
        self.build_form(self.form_layout)
        self.form_layout.addStretch(1)
        splitter.addWidget(form_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Хук для master-detail: подклассы могут добавить под основным
        # сплиттером свою подчинённую таблицу.
        self.build_detail(outer)

        # Кнопки
        buttons = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_update = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_clear = QPushButton("Очистить")
        self.btn_print = QPushButton("Печать")
        self.btn_close = QPushButton("Назад")
        self.btn_add.clicked.connect(self._on_add)
        self.btn_update.clicked.connect(self._on_update)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_print.clicked.connect(self._on_print)
        self.btn_close.clicked.connect(self.close)
        self.btn_delete.setProperty("role", "danger")
        for b in (self.btn_clear, self.btn_print, self.btn_close):
            b.setProperty("role", "secondary")
        # Опциональная кнопка «Карточка» (печать одной сущности).
        self.btn_card: QPushButton | None = None
        if self.supports_card():
            self.btn_card = QPushButton("Карточка")
            self.btn_card.setProperty("role", "secondary")
            self.btn_card.clicked.connect(self._on_card)
        for b in (self.btn_add, self.btn_update, self.btn_delete,
                  self.btn_clear, self.btn_print):
            buttons.addWidget(b)
        if self.btn_card is not None:
            buttons.addWidget(self.btn_card)
        buttons.addWidget(self.btn_close)
        outer.addLayout(buttons)

    # ----------------------------------------------------- override hooks --
    def fetch(self, query: str | None) -> list[dict]:
        raise NotImplementedError

    def build_form(self, layout: QVBoxLayout) -> None:
        raise NotImplementedError

    def build_detail(self, parent_layout: QVBoxLayout) -> None:  # noqa: D401
        """Опционально: подчинённая таблица под основной (master-detail)."""
        return

    def get_form_data(self) -> dict[str, Any]:
        raise NotImplementedError

    def set_form_data(self, row: dict) -> None:
        raise NotImplementedError

    def clear_form(self) -> None:
        raise NotImplementedError

    def insert(self, data: dict[str, Any]) -> None:
        raise NotImplementedError

    def update(self, pk: int, data: dict[str, Any]) -> None:
        raise NotImplementedError

    def remove(self, pk: int) -> None:
        raise NotImplementedError

    # --------------------------------------------------------- внутренние --
    def refresh(self) -> None:
        query = self.search_input.text().strip() or None
        self._rows = self.fetch(query)
        self.table.setRowCount(len(self._rows))
        for r, row in enumerate(self._rows):
            for c, (field, _) in enumerate(self.columns):
                value = row.get(field)
                item = QTableWidgetItem("" if value is None else str(value))
                item.setData(Qt.UserRole, row.get("id"))
                self.table.setItem(r, c, item)

    def _selected_row(self) -> dict | None:
        sel = self.table.currentRow()
        if 0 <= sel < len(self._rows):
            return self._rows[sel]
        return None

    def _on_select(self) -> None:
        row = self._selected_row()
        if row:
            self.set_form_data(row)
            self.on_row_selected(row)

    def on_row_selected(self, row: dict) -> None:  # noqa: D401
        """Хук для подклассов: реакция на выбор строки (master-detail)."""
        return

    def _on_reset_search(self) -> None:
        self.search_input.clear()
        self.refresh()

    def _on_clear(self) -> None:
        self.table.clearSelection()
        self.clear_form()

    def _on_add(self) -> None:
        try:
            data = self.get_form_data()
            self.insert(data)
        except ValueError as exc:
            QMessageBox.warning(self, "Проверка", str(exc))
            return
        except psycopg2.Error as exc:
            QMessageBox.critical(self, "Ошибка БД", str(exc))
            return
        self.clear_form()
        self.refresh()
        QMessageBox.information(self, "Готово", "Запись добавлена.")

    def _on_update(self) -> None:
        row = self._selected_row()
        if not row:
            QMessageBox.warning(self, "Внимание", "Сначала выберите строку в таблице.")
            return
        try:
            data = self.get_form_data()
            self.update(row["id"], data)
        except ValueError as exc:
            QMessageBox.warning(self, "Проверка", str(exc))
            return
        except psycopg2.Error as exc:
            QMessageBox.critical(self, "Ошибка БД", str(exc))
            return
        self.refresh()
        QMessageBox.information(self, "Готово", "Запись обновлена.")

    def _on_delete(self) -> None:
        row = self._selected_row()
        if not row:
            QMessageBox.warning(self, "Внимание", "Сначала выберите строку в таблице.")
            return
        confirm = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить запись №{row['id']}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.remove(row["id"])
        except psycopg2.Error as exc:
            QMessageBox.critical(self, "Ошибка БД", str(exc))
            return
        self.clear_form()
        self.refresh()
        QMessageBox.information(self, "Готово", "Запись удалена.")

    def _on_print(self) -> None:
        from app.reports.printer import print_table
        print_table(self, self.title, [c[1] for c in self.columns],
                    [c[0] for c in self.columns], self._rows)

    # --- override-хуки для «Карточки» одной записи (печатная форма) ---------
    def supports_card(self) -> bool:  # noqa: D401
        """Подкласс возвращает True, если для него есть карточка одной записи."""
        return False

    def render_card(self, row: dict) -> None:  # noqa: D401
        """Подкласс реализует вызов app.reports.printer.print_card(...)."""
        raise NotImplementedError

    def _on_card(self) -> None:
        row = self._selected_row()
        if not row:
            QMessageBox.warning(self, "Внимание",
                                "Выберите запись в таблице, чтобы напечатать карточку.")
            return
        self.render_card(row)
