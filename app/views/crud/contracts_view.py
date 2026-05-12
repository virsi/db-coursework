"""CRUD-форма «Договоры»."""

from datetime import date

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QFormLayout, QVBoxLayout,
)

from app.db.repositories.contracts import ContractsRepository
from app.db.repositories.employees import EmployeesRepository
from app.db.repositories.students import StudentsRepository
from app.db.repositories.teachers import TeachersRepository
from app.views.crud._base_crud import CrudView


class ContractsView(CrudView):
    title = "Договоры"
    columns = (
        ("id",            "ID"),
        ("contract_type", "Тип"),
        ("employee_name", "Сотрудник"),
        ("student_name",  "Студент"),
        ("teacher_name",  "Преподаватель"),
        ("contract_date", "Дата"),
        ("is_active",     "Активен"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.type_input = QComboBox()
        for code, label in ContractsRepository.TYPES:
            self.type_input.addItem(label, code)
        self.type_input.currentIndexChanged.connect(self._refresh_counterparty_state)

        self.employee_input = QComboBox()
        for eid, ename in EmployeesRepository.options():
            self.employee_input.addItem(ename, eid)

        self.student_input = QComboBox()
        for s in StudentsRepository.list():
            self.student_input.addItem(s["full_name"], s["id"])

        self.teacher_input = QComboBox()
        for tid, tname in TeachersRepository.options():
            self.teacher_input.addItem(tname, tid)

        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.active_input = QCheckBox("Договор активен")
        self.active_input.setChecked(True)

        form.addRow("Тип договора:", self.type_input)
        form.addRow("Сотрудник:",    self.employee_input)
        form.addRow("Студент:",      self.student_input)
        form.addRow("Преподаватель:", self.teacher_input)
        form.addRow("Дата:",         self.date_input)
        form.addRow("",              self.active_input)
        layout.addLayout(form)

        self._refresh_counterparty_state()

    def _refresh_counterparty_state(self) -> None:
        """Активна одна сторона договора в зависимости от его типа."""
        is_education = self.type_input.currentData() == "education"
        self.student_input.setEnabled(is_education)
        self.teacher_input.setEnabled(not is_education)

    def fetch(self, query):
        return ContractsRepository.listing(query)

    def get_form_data(self):
        contract_type = self.type_input.currentData()
        return {
            "employee_id":   self.employee_input.currentData(),
            "student_id":    self.student_input.currentData() if contract_type == "education" else None,
            "teacher_id":    self.teacher_input.currentData() if contract_type == "employment" else None,
            "contract_type": contract_type,
            "contract_date": self.date_input.date().toPyDate(),
            "is_active":     self.active_input.isChecked(),
        }

    def set_form_data(self, row):
        idx = self.type_input.findData(row.get("contract_type"))
        if idx >= 0:
            self.type_input.setCurrentIndex(idx)
        idx = self.employee_input.findData(row.get("employee_id"))
        if idx >= 0:
            self.employee_input.setCurrentIndex(idx)
        if row.get("student_id"):
            idx = self.student_input.findData(row.get("student_id"))
            if idx >= 0:
                self.student_input.setCurrentIndex(idx)
        if row.get("teacher_id"):
            idx = self.teacher_input.findData(row.get("teacher_id"))
            if idx >= 0:
                self.teacher_input.setCurrentIndex(idx)
        d = row.get("contract_date") or date.today()
        self.date_input.setDate(QDate(d.year, d.month, d.day))
        self.active_input.setChecked(bool(row.get("is_active", True)))
        self._refresh_counterparty_state()

    def clear_form(self):
        self.type_input.setCurrentIndex(0)
        self.employee_input.setCurrentIndex(0)
        self.student_input.setCurrentIndex(0)
        self.teacher_input.setCurrentIndex(0)
        self.date_input.setDate(QDate.currentDate())
        self.active_input.setChecked(True)
        self._refresh_counterparty_state()

    def insert(self, data):
        ContractsRepository.create(**data)

    def update(self, pk, data):
        ContractsRepository.update(pk, **data)

    def remove(self, pk):
        ContractsRepository.delete(pk)
