"""CRUD-форма «Студенты»."""

from datetime import date

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QComboBox, QDateEdit, QFormLayout, QLineEdit, QVBoxLayout

from app.db.repositories.students import StudentsRepository
from app.reports.printer import print_card
from app.services.reports import student_grades
from app.views.crud._base_crud import CrudView


_STATUS_LABEL = dict(StudentsRepository.STATUSES)


class StudentsView(CrudView):
    title = "Студенты"
    columns = (
        ("id",              "ID"),
        ("full_name",       "ФИО"),
        ("enrollment_date", "Дата зачисления"),
        ("status",          "Статус"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("логин для входа")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("пароль (только при создании)")
        self.full_name_input = QLineEdit()
        self.enrollment_input = QDateEdit(QDate.currentDate())
        self.enrollment_input.setCalendarPopup(True)
        self.enrollment_input.setDisplayFormat("dd.MM.yyyy")
        self.status_input = QComboBox()
        for code, label in StudentsRepository.STATUSES:
            self.status_input.addItem(label, code)

        form.addRow("Логин:",          self.login_input)
        form.addRow("Пароль:",         self.password_input)
        form.addRow("ФИО:",            self.full_name_input)
        form.addRow("Дата зачисления:", self.enrollment_input)
        form.addRow("Статус:",         self.status_input)
        layout.addLayout(form)

    # ----------------------------------------------------------- логика --
    def fetch(self, query):
        return StudentsRepository.search(query)

    def get_form_data(self):
        full_name = self.full_name_input.text().strip()
        if not full_name:
            raise ValueError("Поле «ФИО» обязательно для заполнения.")
        return {
            "login":           self.login_input.text().strip(),
            "password":        self.password_input.text(),
            "full_name":       full_name,
            "enrollment_date": self.enrollment_input.date().toPyDate(),
            "status":          self.status_input.currentData(),
        }

    def set_form_data(self, row):
        self.login_input.setText("")           # логин нельзя редактировать здесь
        self.login_input.setEnabled(False)
        self.password_input.setText("")
        self.password_input.setEnabled(False)
        self.full_name_input.setText(row.get("full_name", ""))
        d = row.get("enrollment_date") or date.today()
        self.enrollment_input.setDate(QDate(d.year, d.month, d.day))
        idx = self.status_input.findData(row.get("status"))
        if idx >= 0:
            self.status_input.setCurrentIndex(idx)

    def clear_form(self):
        self.login_input.clear()
        self.login_input.setEnabled(True)
        self.password_input.clear()
        self.password_input.setEnabled(True)
        self.full_name_input.clear()
        self.enrollment_input.setDate(QDate.currentDate())
        self.status_input.setCurrentIndex(0)

    def insert(self, data):
        if not data["login"] or not data["password"]:
            raise ValueError("Для нового студента укажите логин и пароль.")
        StudentsRepository.create_with_user(
            login=data["login"], password=data["password"],
            full_name=data["full_name"],
            enrollment_date=data["enrollment_date"], status=data["status"],
        )

    def update(self, pk, data):
        StudentsRepository.update(pk,
            full_name=data["full_name"],
            enrollment_date=data["enrollment_date"],
            status=data["status"])

    def remove(self, pk):
        StudentsRepository.delete_with_user(pk)

    # --------------------------------------------------- Карточка студента --
    def supports_card(self) -> bool:
        return True

    def render_card(self, row: dict) -> None:
        student_id = row.get("id")
        full_name = row.get("full_name") or "—"
        status_code = row.get("status")
        status = _STATUS_LABEL.get(
            status_code.value if hasattr(status_code, "value") else status_code,
            str(status_code) if status_code else "—",
        )
        enrolled = row.get("enrollment_date")
        enrolled_text = (
            enrolled.strftime("%d.%m.%Y") if hasattr(enrolled, "strftime")
            else (str(enrolled) if enrolled else "—")
        )

        grades = student_grades(student_id)
        detail_rows = [
            (
                g.get("course_name") or "",
                g.get("task_title") or "",
                str(g.get("task_type") or ""),
                f"{g.get('score', 0)}/{g.get('max_score', 100)}",
                (g.get("graded_at").strftime("%d.%m.%Y")
                 if hasattr(g.get("graded_at"), "strftime") else "—"),
            )
            for g in grades
        ]
        avg_score = (
            f"{sum(g['score'] for g in grades) / len(grades):.2f}"
            if grades else "—"
        )

        print_card(
            self,
            title="Карточка студента",
            header=full_name,
            rows=[
                ("Идентификатор",   str(student_id)),
                ("ФИО",             full_name),
                ("Статус обучения", status),
                ("Дата зачисления", enrolled_text),
                ("Всего оценок",    str(len(grades))),
                ("Средний балл",    avg_score),
            ],
            detail_title=f"Оценки студента ({len(grades)} записей)",
            detail_headers=("Курс", "Задание", "Тип", "Балл", "Дата"),
            detail_rows=detail_rows,
        )
