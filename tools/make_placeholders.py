"""Генерация PNG-плейсхолдеров для UI-скриншотов АС ОУДО.

Запускается до того, как сделаны реальные снимки. Каждый файл —
монотонный фон с подписью, чтобы РПЗ.docx собирался корректно.
После того как реальные скриншоты сделаны, заглушки заменяются ими.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"

PLACEHOLDERS: list[tuple[str, str]] = [
    ("01_login",                       "Окно авторизации"),
    ("02_login_error",                 "Ошибка авторизации"),
    ("03_menu_admin",                  "Главное меню сотрудника"),
    ("04_menu_teacher",                "Главное меню преподавателя"),
    ("05_menu_student",                "Главное меню студента"),
    ("10_students_list",               "Форма «Студенты»"),
    ("11_students_add",                "Форма «Студенты» — добавление записи"),
    ("12_students_search",             "Форма «Студенты» — поиск"),
    ("13_teachers",                    "Форма «Преподаватели»"),
    ("14_employees",                   "Форма «Сотрудники»"),
    ("15_disciplines",                 "Форма «Дисциплины»"),
    ("16_courses",                     "Форма «Курсы»"),
    ("17_enrollments",                 "Форма «Запись на курс»"),
    ("18_contracts",                   "Форма «Договоры»"),
    ("19_tasks",                       "Форма «Задания»"),
    ("20_variants",                    "Форма «Варианты»"),
    ("21_grades",                      "Форма «Оценки»"),
    ("30_report_courses",              "Отчёт «Список курсов»"),
    ("31_report_enrollments",          "Отчёт «Сводка по записи»"),
    ("32_report_teachers",             "Отчёт «Преподаватели и курсы»"),
    ("33_report_avg_course",           "Отчёт «Средний балл по курсу»"),
    ("34_report_100",                  "Отчёт «100-балльная система»"),
    ("35_report_student_grades",       "Отчёт «Баллы студента»"),
    ("36_report_student_courses",      "Отчёт «Мои курсы» (студент)"),
    ("40_print_preview",               "Предпросмотр печати"),
    ("50_msg_added",                   "Сообщение «Запись добавлена»"),
    ("51_msg_validation",              "Предупреждение валидации"),
    ("52_msg_delete_confirm",          "Подтверждение удаления"),
    ("60_db_connect_error",            "Ошибка подключения к БД"),
]

WIDTH, HEIGHT = 1280, 800
BG = "#f8fafc"
BORDER = "#94a3b8"
TEXT = "#0f172a"
SUBTEXT = "#475569"


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",      # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",   # Linux
        "C:\\Windows\\Fonts\\arial.ttf",                       # Windows
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make(name: str, title: str) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([8, 8, WIDTH - 8, HEIGHT - 8], outline=BORDER, width=4)

    title_font = _font(56)
    sub_font = _font(28)
    note_font = _font(22)

    draw.text((WIDTH // 2, HEIGHT // 2 - 80),
              "📷  СКРИНШОТ-ЗАГЛУШКА",
              fill=BORDER, anchor="mm", font=sub_font)
    draw.text((WIDTH // 2, HEIGHT // 2),
              title, fill=TEXT, anchor="mm", font=title_font)
    draw.text((WIDTH // 2, HEIGHT // 2 + 80),
              f"docs/screenshots/{name}.png",
              fill=SUBTEXT, anchor="mm", font=sub_font)
    draw.text((WIDTH // 2, HEIGHT - 40),
              "Заменить файлом реального снимка интерфейса перед сдачей",
              fill=SUBTEXT, anchor="mm", font=note_font)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.png"
    if out.exists():
        return
    img.save(out, optimize=True)
    print(f"  + {out.relative_to(OUT_DIR.parent.parent)}")


def main() -> None:
    print("Генерирую плейсхолдеры скриншотов:")
    for name, title in PLACEHOLDERS:
        make(name, title)
    print("Готово.")


if __name__ == "__main__":
    main()
