"""Глобальная тема приложения АС ОУДО.

Применяется в main.py до создания окон. Делает UI консистентным независимо
от системной темы macOS/Linux/Windows и устраняет проблему серых кнопок
в Dark Mode на macOS.
"""

# Палитра в стиле «корпоративный синий».
PRIMARY        = "#2563eb"   # синий — кнопка действия
PRIMARY_HOVER  = "#1d4ed8"
PRIMARY_PRESS  = "#1e40af"

DANGER         = "#dc2626"   # красный — удаление
DANGER_HOVER   = "#b91c1c"
DANGER_PRESS   = "#991b1b"

NEUTRAL        = "#f8fafc"   # светло-серый фон окон
SURFACE        = "#ffffff"   # белый фон таблиц/полей
BORDER         = "#cbd5e1"   # серая рамка
BORDER_FOCUS   = "#2563eb"
TEXT           = "#0f172a"
TEXT_MUTED     = "#64748b"
HEADER_BG      = "#e2e8f0"
SELECTION_BG   = "#dbeafe"


QSS = f"""
/* ---------- Базовые цвета ----------------------------------------- */
QWidget {{
    background-color: {NEUTRAL};
    color: {TEXT};
    font-family: -apple-system, "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QLabel {{
    background: transparent;
}}

/* ---------- Кнопки ------------------------------------------------- */
QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: 1px solid {PRIMARY_HOVER};
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
    border-color: {PRIMARY_PRESS};
}}
QPushButton:pressed {{
    background-color: {PRIMARY_PRESS};
}}
QPushButton:disabled {{
    background-color: #94a3b8;
    border-color: #94a3b8;
    color: #e2e8f0;
}}
QPushButton:default {{
    background-color: {PRIMARY_PRESS};
    border-color: {PRIMARY_PRESS};
}}

/* «Опасные» кнопки — Удалить, Выйти из приложения. */
QPushButton[role="danger"] {{
    background-color: {DANGER};
    border-color: {DANGER_HOVER};
}}
QPushButton[role="danger"]:hover {{
    background-color: {DANGER_HOVER};
}}
QPushButton[role="danger"]:pressed {{
    background-color: {DANGER_PRESS};
}}

/* «Вторичные» кнопки — Назад, Очистить, Сброс. */
QPushButton[role="secondary"] {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QPushButton[role="secondary"]:hover {{
    background-color: {HEADER_BG};
}}
QPushButton[role="secondary"]:pressed {{
    background-color: {BORDER};
}}

/* ---------- Поля ввода -------------------------------------------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDateEdit, QDateTimeEdit, QComboBox {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {SELECTION_BG};
    selection-color: {TEXT};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDateEdit:focus, QDateTimeEdit:focus, QComboBox:focus {{
    border-color: {BORDER_FOCUS};
}}
QLineEdit:disabled, QSpinBox:disabled, QDateEdit:disabled,
QDateTimeEdit:disabled, QComboBox:disabled {{
    background-color: {HEADER_BG};
    color: {TEXT_MUTED};
}}

QComboBox::drop-down {{
    width: 18px;
    border: none;
}}

QCheckBox {{
    spacing: 6px;
}}

/* ---------- Таблицы ------------------------------------------------ */
QTableWidget, QTableView {{
    background-color: {SURFACE};
    alternate-background-color: #f1f5f9;
    gridline-color: {BORDER};
    selection-background-color: {SELECTION_BG};
    selection-color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}
QHeaderView::section {{
    background-color: {HEADER_BG};
    color: {TEXT};
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}
QTableCornerButton::section {{
    background-color: {HEADER_BG};
    border: 1px solid {BORDER};
}}

/* ---------- Группы и сплиттеры ----------------------------------- */
QSplitter::handle {{
    background-color: {BORDER};
    width: 1px;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {TEXT_MUTED};
}}

/* ---------- Сообщения --------------------------------------------- */
QMessageBox {{
    background-color: {NEUTRAL};
}}
QMessageBox QPushButton {{
    min-width: 80px;
}}
"""


def apply_theme(app) -> None:
    """Применить общий стиль приложения."""
    from PyQt5.QtWidgets import QStyleFactory
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
    app.setStyleSheet(QSS)
