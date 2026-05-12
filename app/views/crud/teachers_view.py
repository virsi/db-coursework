"""CRUD-форма «Преподаватели»."""

from PyQt5.QtWidgets import QFormLayout, QLineEdit, QVBoxLayout

from app.db.repositories.teachers import TeachersRepository
from app.views.crud._base_crud import CrudView


class TeachersView(CrudView):
    title = "Преподаватели"
    columns = (
        ("id",             "ID"),
        ("full_name",      "ФИО"),
        ("position",       "Должность"),
        ("specialization", "Специализация"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.full_name_input = QLineEdit()
        self.position_input = QLineEdit()
        self.spec_input = QLineEdit()

        form.addRow("Логин:",         self.login_input)
        form.addRow("Пароль:",        self.password_input)
        form.addRow("ФИО:",           self.full_name_input)
        form.addRow("Должность:",     self.position_input)
        form.addRow("Специализация:", self.spec_input)
        layout.addLayout(form)

    def fetch(self, query):
        return TeachersRepository.search(query)

    def get_form_data(self):
        full_name = self.full_name_input.text().strip()
        position = self.position_input.text().strip()
        specialization = self.spec_input.text().strip()
        if not full_name or not position or not specialization:
            raise ValueError("ФИО, должность и специализация обязательны.")
        return {
            "login":          self.login_input.text().strip(),
            "password":       self.password_input.text(),
            "full_name":      full_name,
            "position":       position,
            "specialization": specialization,
        }

    def set_form_data(self, row):
        self.login_input.setText("")
        self.login_input.setEnabled(False)
        self.password_input.setText("")
        self.password_input.setEnabled(False)
        self.full_name_input.setText(row.get("full_name", ""))
        self.position_input.setText(row.get("position", ""))
        self.spec_input.setText(row.get("specialization", ""))

    def clear_form(self):
        self.login_input.clear(); self.login_input.setEnabled(True)
        self.password_input.clear(); self.password_input.setEnabled(True)
        self.full_name_input.clear()
        self.position_input.clear()
        self.spec_input.clear()

    def insert(self, data):
        if not data["login"] or not data["password"]:
            raise ValueError("Для нового преподавателя укажите логин и пароль.")
        TeachersRepository.create_with_user(
            login=data["login"], password=data["password"],
            full_name=data["full_name"],
            position=data["position"], specialization=data["specialization"],
        )

    def update(self, pk, data):
        TeachersRepository.update(pk,
            full_name=data["full_name"],
            position=data["position"],
            specialization=data["specialization"])

    def remove(self, pk):
        TeachersRepository.delete_with_user(pk)
