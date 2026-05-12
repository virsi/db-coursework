"""CRUD-форма «Сотрудники»."""

from PyQt5.QtWidgets import QComboBox, QFormLayout, QLineEdit, QVBoxLayout

from app.db.repositories.employees import EmployeesRepository
from app.views.crud._base_crud import CrudView


class EmployeesView(CrudView):
    title = "Сотрудники"
    columns = (
        ("id",           "ID"),
        ("full_name",    "ФИО"),
        ("position",     "Должность"),
        ("access_level", "Уровень доступа"),
    )

    def build_form(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.full_name_input = QLineEdit()
        self.position_input = QLineEdit()
        self.access_input = QComboBox()
        for code, label in EmployeesRepository.ACCESS_LEVELS:
            self.access_input.addItem(label, code)

        form.addRow("Логин:",          self.login_input)
        form.addRow("Пароль:",         self.password_input)
        form.addRow("ФИО:",            self.full_name_input)
        form.addRow("Должность:",      self.position_input)
        form.addRow("Уровень доступа:", self.access_input)
        layout.addLayout(form)

    def fetch(self, query):
        return EmployeesRepository.search(query)

    def get_form_data(self):
        full_name = self.full_name_input.text().strip()
        position = self.position_input.text().strip()
        if not full_name or not position:
            raise ValueError("ФИО и должность обязательны.")
        return {
            "login":        self.login_input.text().strip(),
            "password":     self.password_input.text(),
            "full_name":    full_name,
            "position":     position,
            "access_level": self.access_input.currentData(),
        }

    def set_form_data(self, row):
        self.login_input.setText(""); self.login_input.setEnabled(False)
        self.password_input.setText(""); self.password_input.setEnabled(False)
        self.full_name_input.setText(row.get("full_name", ""))
        self.position_input.setText(row.get("position", ""))
        idx = self.access_input.findData(row.get("access_level"))
        if idx >= 0:
            self.access_input.setCurrentIndex(idx)

    def clear_form(self):
        self.login_input.clear(); self.login_input.setEnabled(True)
        self.password_input.clear(); self.password_input.setEnabled(True)
        self.full_name_input.clear()
        self.position_input.clear()
        self.access_input.setCurrentIndex(0)

    def insert(self, data):
        if not data["login"] or not data["password"]:
            raise ValueError("Для нового сотрудника укажите логин и пароль.")
        EmployeesRepository.create_with_user(
            login=data["login"], password=data["password"],
            full_name=data["full_name"],
            position=data["position"], access_level=data["access_level"],
        )

    def update(self, pk, data):
        EmployeesRepository.update(pk,
            full_name=data["full_name"],
            position=data["position"],
            access_level=data["access_level"])

    def remove(self, pk):
        EmployeesRepository.delete_with_user(pk)
