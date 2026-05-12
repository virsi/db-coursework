"""CRUD-форма «Дисциплины»."""

from PyQt5.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QTextEdit, QVBoxLayout

from app.db.repositories.disciplines import DisciplinesRepository
from app.views.crud._base_crud import CrudView


class DisciplinesView(CrudView):
    title = "Дисциплины"
    columns = (
        ("id",          "ID"),
        ("name",        "Наименование"),
        ("hours",       "Часы"),
        ("description", "Описание"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.hours_input = QSpinBox()
        self.hours_input.setRange(1, 1000)
        self.hours_input.setValue(72)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(120)

        form.addRow("Наименование:", self.name_input)
        form.addRow("Часы:",         self.hours_input)
        form.addRow("Описание:",     self.description_input)
        layout.addLayout(form)

    def fetch(self, query):
        return DisciplinesRepository.search(query)

    def get_form_data(self):
        name = self.name_input.text().strip()
        if not name:
            raise ValueError("Наименование обязательно.")
        return {
            "name":        name,
            "hours":       self.hours_input.value(),
            "description": self.description_input.toPlainText().strip() or None,
        }

    def set_form_data(self, row):
        self.name_input.setText(row.get("name", ""))
        self.hours_input.setValue(int(row.get("hours") or 1))
        self.description_input.setPlainText(row.get("description") or "")

    def clear_form(self):
        self.name_input.clear()
        self.hours_input.setValue(72)
        self.description_input.clear()

    def insert(self, data):
        DisciplinesRepository.create(**data)

    def update(self, pk, data):
        DisciplinesRepository.update(pk, **data)

    def remove(self, pk):
        DisciplinesRepository.delete(pk)
