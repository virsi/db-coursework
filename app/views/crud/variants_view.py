"""CRUD-форма «Варианты заданий»."""

from PyQt5.QtWidgets import (
    QComboBox, QFormLayout, QSpinBox, QTextEdit, QVBoxLayout,
)

from app.db.repositories.tasks import TasksRepository
from app.db.repositories.variants import VariantsRepository
from app.views.crud._base_crud import CrudView


class VariantsView(CrudView):
    title = "Варианты заданий"
    columns = (
        ("id",          "ID"),
        ("task_title",  "Задание"),
        ("number",      "Номер"),
        ("description", "Описание"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.task_input = QComboBox()
        for t in TasksRepository.listing():
            self.task_input.addItem(t["title"], t["id"])
        self.number_input = QSpinBox()
        self.number_input.setRange(1, 99)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(160)

        form.addRow("Задание:",  self.task_input)
        form.addRow("Номер:",    self.number_input)
        form.addRow("Описание:", self.description_input)
        layout.addLayout(form)

    def fetch(self, query):
        return VariantsRepository.listing(query)

    def get_form_data(self):
        description = self.description_input.toPlainText().strip()
        if not description:
            raise ValueError("Описание варианта обязательно.")
        return {
            "task_id":     self.task_input.currentData(),
            "number":      self.number_input.value(),
            "description": description,
        }

    def set_form_data(self, row):
        idx = self.task_input.findData(row.get("task_id"))
        if idx >= 0:
            self.task_input.setCurrentIndex(idx)
        self.number_input.setValue(int(row.get("number") or 1))
        self.description_input.setPlainText(row.get("description") or "")

    def clear_form(self):
        self.task_input.setCurrentIndex(0)
        self.number_input.setValue(1)
        self.description_input.clear()

    def insert(self, data):
        VariantsRepository.create(**data)

    def update(self, pk, data):
        VariantsRepository.update(pk, **data)

    def remove(self, pk):
        VariantsRepository.delete(pk)
