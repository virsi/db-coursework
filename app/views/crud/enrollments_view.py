"""CRUD-форма «Запись на курс»."""

from datetime import date

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QFormLayout, QVBoxLayout,
)

from app.db.repositories.courses import CoursesRepository
from app.db.repositories.enrollments import EnrollmentsRepository
from app.db.repositories.students import StudentsRepository
from app.views.crud._base_crud import CrudView


class EnrollmentsView(CrudView):
    title = "Запись на курс"
    columns = (
        ("id",              "ID"),
        ("student_name",    "Студент"),
        ("course_name",     "Курс"),
        ("enrollment_date", "Дата записи"),
        ("is_active",       "Активна"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.student_input = QComboBox()
        for s in StudentsRepository.list():
            self.student_input.addItem(s["full_name"], s["id"])
        self.course_input = QComboBox()
        for cid, cname in CoursesRepository.options():
            self.course_input.addItem(cname, cid)
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.active_input = QCheckBox("Запись активна")
        self.active_input.setChecked(True)

        form.addRow("Студент:",     self.student_input)
        form.addRow("Курс:",        self.course_input)
        form.addRow("Дата записи:", self.date_input)
        form.addRow("",             self.active_input)
        layout.addLayout(form)

    def fetch(self, query):
        return EnrollmentsRepository.listing(query)

    def get_form_data(self):
        return {
            "student_id":      self.student_input.currentData(),
            "course_id":       self.course_input.currentData(),
            "enrollment_date": self.date_input.date().toPyDate(),
            "is_active":       self.active_input.isChecked(),
        }

    def set_form_data(self, row):
        idx = self.student_input.findData(row.get("student_id"))
        if idx >= 0:
            self.student_input.setCurrentIndex(idx)
        idx = self.course_input.findData(row.get("course_id"))
        if idx >= 0:
            self.course_input.setCurrentIndex(idx)
        d = row.get("enrollment_date") or date.today()
        self.date_input.setDate(QDate(d.year, d.month, d.day))
        self.active_input.setChecked(bool(row.get("is_active", True)))

    def clear_form(self):
        self.student_input.setCurrentIndex(0)
        self.course_input.setCurrentIndex(0)
        self.date_input.setDate(QDate.currentDate())
        self.active_input.setChecked(True)

    def insert(self, data):
        EnrollmentsRepository.create(**data)

    def update(self, pk, data):
        EnrollmentsRepository.update(pk, **data)

    def remove(self, pk):
        EnrollmentsRepository.delete(pk)
