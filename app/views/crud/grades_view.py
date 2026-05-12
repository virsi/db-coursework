"""CRUD-форма «Оценки»."""

from datetime import datetime

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import (
    QComboBox, QDateTimeEdit, QFormLayout, QSpinBox, QVBoxLayout,
)

from app.db.repositories.grades import GradesRepository
from app.db.repositories.students import StudentsRepository
from app.db.repositories.tasks import TasksRepository
from app.views.crud._base_crud import CrudView


class GradesView(CrudView):
    title = "Оценки"
    columns = (
        ("id",            "ID"),
        ("student_name",  "Студент"),
        ("course_name",   "Курс"),
        ("task_title",    "Задание"),
        ("score",         "Балл"),
        ("graded_at",     "Дата выставления"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.student_input = QComboBox()
        for s in StudentsRepository.list():
            self.student_input.addItem(s["full_name"], s["id"])
        self.task_input = QComboBox()
        for t in TasksRepository.listing():
            self.task_input.addItem(f"{t['course_name']} — {t['title']}", t["id"])
        self.score_input = QSpinBox()
        self.score_input.setRange(0, 100)
        self.score_input.setValue(80)
        self.graded_at_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.graded_at_input.setCalendarPopup(True)
        self.graded_at_input.setDisplayFormat("dd.MM.yyyy HH:mm")

        form.addRow("Студент:",          self.student_input)
        form.addRow("Задание:",          self.task_input)
        form.addRow("Балл (0–100):",     self.score_input)
        form.addRow("Дата выставления:", self.graded_at_input)
        layout.addLayout(form)

    def fetch(self, query):
        return GradesRepository.listing(query)

    def get_form_data(self):
        return {
            "student_id": self.student_input.currentData(),
            "task_id":    self.task_input.currentData(),
            "score":      self.score_input.value(),
            "graded_at":  self.graded_at_input.dateTime().toPyDateTime(),
        }

    def set_form_data(self, row):
        idx = self.student_input.findData(row.get("student_id"))
        if idx >= 0:
            self.student_input.setCurrentIndex(idx)
        idx = self.task_input.findData(row.get("task_id"))
        if idx >= 0:
            self.task_input.setCurrentIndex(idx)
        self.score_input.setValue(int(row.get("score") or 0))
        ga = row.get("graded_at")
        if isinstance(ga, datetime):
            self.graded_at_input.setDateTime(QDateTime(ga))

    def clear_form(self):
        self.student_input.setCurrentIndex(0)
        self.task_input.setCurrentIndex(0)
        self.score_input.setValue(80)
        self.graded_at_input.setDateTime(QDateTime.currentDateTime())

    def insert(self, data):
        GradesRepository.create(**data)

    def update(self, pk, data):
        GradesRepository.update(pk, **data)

    def remove(self, pk):
        GradesRepository.delete(pk)
