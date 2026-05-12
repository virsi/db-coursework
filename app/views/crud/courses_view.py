"""CRUD-форма «Курсы» с подчинённой таблицей «Задания курса» (master-detail)."""

from datetime import date

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QFormLayout, QHeaderView, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from app.db.repositories.courses import CoursesRepository
from app.db.repositories.disciplines import DisciplinesRepository
from app.db.repositories.tasks import TasksRepository
from app.db.repositories.teachers import TeachersRepository
from app.views.crud._base_crud import CrudView


class CoursesView(CrudView):
    title = "Курсы"
    columns = (
        ("id",              "ID"),
        ("name",            "Название"),
        ("discipline_name", "Дисциплина"),
        ("teacher_name",    "Преподаватель"),
        ("start_date",      "Начало"),
        ("end_date",        "Окончание"),
    )

    DETAIL_COLUMNS = (
        ("title",     "Задание"),
        ("type",      "Тип"),
        ("deadline",  "Срок сдачи"),
        ("max_score", "Макс. балл"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.discipline_input = QComboBox()
        for did, dname in DisciplinesRepository.options():
            self.discipline_input.addItem(dname, did)
        self.teacher_input = QComboBox()
        for tid, tname in TeachersRepository.options():
            self.teacher_input.addItem(tname, tid)
        self.start_input = QDateEdit(QDate.currentDate())
        self.start_input.setCalendarPopup(True)
        self.start_input.setDisplayFormat("dd.MM.yyyy")
        self.end_input = QDateEdit(QDate.currentDate().addMonths(6))
        self.end_input.setCalendarPopup(True)
        self.end_input.setDisplayFormat("dd.MM.yyyy")

        form.addRow("Название:",      self.name_input)
        form.addRow("Дисциплина:",    self.discipline_input)
        form.addRow("Преподаватель:", self.teacher_input)
        form.addRow("Дата начала:",   self.start_input)
        form.addRow("Дата окончания:", self.end_input)
        layout.addLayout(form)

    def fetch(self, query):
        return CoursesRepository.search(query)

    def get_form_data(self):
        name = self.name_input.text().strip()
        if not name:
            raise ValueError("Название курса обязательно.")
        start = self.start_input.date().toPyDate()
        end = self.end_input.date().toPyDate()
        if end <= start:
            raise ValueError("Дата окончания должна быть позже даты начала.")
        return {
            "name":          name,
            "start_date":    start,
            "end_date":      end,
            "teacher_id":    self.teacher_input.currentData(),
            "discipline_id": self.discipline_input.currentData(),
        }

    def set_form_data(self, row):
        self.name_input.setText(row.get("name", ""))
        s = row.get("start_date") or date.today()
        e = row.get("end_date") or date.today()
        self.start_input.setDate(QDate(s.year, s.month, s.day))
        self.end_input.setDate(QDate(e.year, e.month, e.day))
        idx = self.teacher_input.findData(row.get("teacher_id"))
        if idx >= 0:
            self.teacher_input.setCurrentIndex(idx)
        idx = self.discipline_input.findData(row.get("discipline_id"))
        if idx >= 0:
            self.discipline_input.setCurrentIndex(idx)

    def clear_form(self):
        self.name_input.clear()
        self.start_input.setDate(QDate.currentDate())
        self.end_input.setDate(QDate.currentDate().addMonths(6))
        self.teacher_input.setCurrentIndex(0)
        self.discipline_input.setCurrentIndex(0)

    def insert(self, data):
        CoursesRepository.create(**data)

    def update(self, pk, data):
        CoursesRepository.update(pk, **data)

    def remove(self, pk):
        CoursesRepository.delete(pk)

    # ------------------------------------------------------- master-detail --
    def build_detail(self, parent_layout: QVBoxLayout) -> None:
        self._detail_label = QLabel("Задания выбранного курса:")
        self._detail_label.setStyleSheet("color: #555; margin-top: 6px;")
        parent_layout.addWidget(self._detail_label)

        self._detail_table = QTableWidget()
        self._detail_table.setColumnCount(len(self.DETAIL_COLUMNS))
        self._detail_table.setHorizontalHeaderLabels(
            [c[1] for c in self.DETAIL_COLUMNS]
        )
        self._detail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._detail_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self._detail_table.setMaximumHeight(180)
        parent_layout.addWidget(self._detail_table)

    def on_row_selected(self, row: dict) -> None:
        course_id = row.get("id")
        if course_id is None:
            self._detail_table.setRowCount(0)
            return
        tasks = TasksRepository.listing(None, course_id=course_id)
        self._detail_label.setText(
            f"Задания курса «{row.get('name', '')}» — {len(tasks)} шт."
        )
        self._detail_table.setRowCount(len(tasks))
        for r, t in enumerate(tasks):
            for c, (field, _) in enumerate(self.DETAIL_COLUMNS):
                v = t.get(field)
                self._detail_table.setItem(
                    r, c, QTableWidgetItem("" if v is None else str(v))
                )
