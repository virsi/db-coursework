"""CRUD-форма «Задания»."""

from datetime import datetime

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QComboBox, QDateTimeEdit, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QVBoxLayout,
)

from app.db.repositories.courses import CoursesRepository
from app.db.repositories.tasks import TasksRepository
from app.views.crud._base_crud import CrudView


class TasksView(CrudView):
    title = "Задания"
    columns = (
        ("id",          "ID"),
        ("course_name", "Курс"),
        ("title",       "Название"),
        ("type",        "Тип"),
        ("deadline",    "Срок"),
        ("max_score",   "Макс. балл"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.title_input = QLineEdit()
        self.course_input = QComboBox()
        for cid, cname in CoursesRepository.options():
            self.course_input.addItem(cname, cid)
        self.type_input = QComboBox()
        for code, label in TasksRepository.TYPES:
            self.type_input.addItem(label, code)
        self.deadline_input = QDateTimeEdit(QDateTime.currentDateTime().addDays(14))
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.max_score_input = QSpinBox()
        self.max_score_input.setRange(1, 1000)
        self.max_score_input.setValue(100)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(120)

        form.addRow("Название:", self.title_input)
        form.addRow("Курс:",     self.course_input)
        form.addRow("Тип:",      self.type_input)
        form.addRow("Срок:",     self.deadline_input)
        form.addRow("Макс. балл:", self.max_score_input)
        form.addRow("Описание:", self.description_input)
        layout.addLayout(form)

    def fetch(self, query):
        return TasksRepository.listing(query)

    def get_form_data(self):
        title = self.title_input.text().strip()
        if not title:
            raise ValueError("Название задания обязательно.")
        return {
            "title":       title,
            "course_id":   self.course_input.currentData(),
            "type":        self.type_input.currentData(),
            "deadline":    self.deadline_input.dateTime().toPyDateTime(),
            "max_score":   self.max_score_input.value(),
            "description": self.description_input.toPlainText().strip() or None,
        }

    def set_form_data(self, row):
        self.title_input.setText(row.get("title", ""))
        idx = self.course_input.findData(row.get("course_id"))
        if idx >= 0:
            self.course_input.setCurrentIndex(idx)
        idx = self.type_input.findData(row.get("type"))
        if idx >= 0:
            self.type_input.setCurrentIndex(idx)
        dl = row.get("deadline")
        if isinstance(dl, datetime):
            self.deadline_input.setDateTime(QDateTime(dl))
        self.max_score_input.setValue(int(row.get("max_score") or 100))
        self.description_input.setPlainText(row.get("description") or "")

    def clear_form(self):
        self.title_input.clear()
        self.course_input.setCurrentIndex(0)
        self.type_input.setCurrentIndex(0)
        self.deadline_input.setDateTime(QDateTime.currentDateTime().addDays(14))
        self.max_score_input.setValue(100)
        self.description_input.clear()

    def insert(self, data):
        TasksRepository.create(**data)

    def update(self, pk, data):
        TasksRepository.update(pk, **data)

    def remove(self, pk):
        TasksRepository.delete(pk)
