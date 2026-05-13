"""Программная генерация первых четырёх страниц РПЗ.

Воспроизводит точное оформление примера курсовой работы кафедры ИУ5
МГТУ им. Н. Э. Баумана: титульный лист с гербом, задание на выполнение
курсовой работы, календарный план и аннотацию.

Скрипт ищет в собранном `build/Воробьёв_РПЗ.docx` параграф-маркер
`___PREAMBLE_PLACEHOLDER___`, вставляет вместо него четыре страницы
преамбулы и удаляет маркер. Все элементы создаются стандартным API
`python-docx` в конце документа, а затем перемещаются перед маркером,
что гарантирует корректные ссылки на встроенный логотип.

Запуск:
    arch -arm64 .venv/bin/python tools/build_preamble.py
        build/Воробьёв_РПЗ.docx
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "tools" / "assets" / "bmstu_logo.png"

MARKER = "PREAMBLEPLACEHOLDERDONOTEDIT"
TOC_MARKER = "TOCPLACEHOLDERDONOTEDIT"

# ---------------------------------------------------------------- данные ---

STUDENT_FULL = "Воробьёв Егор Александрович"
STUDENT_SHORT = "Воробьёв Е. А."
GROUP = "ИУ5-42Б"
DISCIPLINE = "Базы данных"
THEME = (
    "АС ОУДО на платформе PostgreSQL и PyQt5"
)
YEAR = "2026"
ISSUE_DATE_DAY = "03"
ISSUE_DATE_MONTH = "февраля"
HEAD_OF_DEPARTMENT = "В. И. Терехов"
DEPT_INDEX = "ИУ5"
RPZ_PAGES = "70"

FACULTY = "ИНФОРМАТИКА И СИСТЕМЫ УПРАВЛЕНИЯ"
DEPARTMENT_FULL = "СИСТЕМЫ ОБРАБОТКИ ИНФОРМАЦИИ И УПРАВЛЕНИЯ"

UNIVERSITY_HEADER_LINES = [
    "Министерство науки и высшего образования Российской Федерации",
    "Федеральное государственное автономное образовательное учреждение",
    "высшего образования",
    "«Московский государственный технический университет",
    "имени Н. Э. Баумана",
    "(национальный исследовательский университет)»",
    "(МГТУ им. Н. Э. Баумана)",
]

ASSIGNMENT_ITEMS = [
    "1. Разработать АС ОУДО, отвечающую на запросы о студентах, преподавателях, "
    "сотрудниках, дисциплинах, курсах, договорах, заданиях и оценках "
    "образовательного учреждения дистанционного обучения;",
    "2. В ходе курсового проектирования разработать техническое задание, "
    "функциональную, инфологическую и датологическую модели предметной области, "
    "интерфейс пользователя, структурную схему, схему работы системы, граф "
    "диалога, методику испытаний и руководство пользователя.",
    "3. В ходе лабораторного практикума выполнить практическую реализацию "
    "автоматизированной информационной системы.",
]

GRAPHIC_SHEETS = [
    "Лист 1. Изображение предметной области",
    "Лист 2. Диаграмма DFD функциональной модели предметной области",
    "Лист 3. Диаграмма IDEF0 функциональной модели предметной области",
    "Лист 4. Инфологическая модель предметной области (графическая диаграмма)",
    "Лист 5. Датологическая модель предметной области (графическая диаграмма)",
    "Лист 6. Схема работы системы",
    "Лист 7. Структурная схема АС ОУДО",
    "Лист 8. Граф диалога системы",
]

CALENDAR_ROWS = [
    ("1.", "Задание на выполнение курсовой работы", "03.02.2026"),
    ("2.", "1 модуль",                              "21.03.2026"),
    ("3.", "2 модуль",                              "25.04.2026"),
    ("4.", "Оформление РПЗ (Отчёта)",               "10.05.2026"),
    ("5.", "Подготовка доклада и презентации\n(при необходимости)",
                                                    "20.05.2026"),
    ("6.", "Защита курсовой работы",                "30.05.2026"),
]

ANNOTATION_PARAGRAPHS = [
    "АС ОУДО разработана для автоматизации работы с информацией о студентах, "
    "преподавателях, сотрудниках, дисциплинах, курсах, договорах, заданиях и "
    "оценках образовательного учреждения дистанционного обучения.",
    "Система позволяет администраторам и преподавателям управлять "
    "справочниками, регистрировать студентов, выдавать задания и формировать "
    "отчёты по успеваемости, а студентам — просматривать собственные курсы, "
    "ознакамливаться с заданиями и видеть итоговые оценки.",
    "Программный продукт представляет собой базу данных под управлением "
    "СУБД PostgreSQL 17 и кроссплатформенное настольное приложение на "
    "PyQt5, обеспечивающее удобный пользовательский интерфейс с "
    "разграничением прав по трём ролям: администратор, преподаватель, студент.",
]


# ----------------------------------------------------------- утилиты OXML --

def _qn(tag: str) -> str:
    return qn(tag)


def set_run_font(run, *, size: float = 14.0, bold: bool = False,
                 italic: bool = False, underline: bool = False,
                 all_caps: bool = False,
                 spacing_pt: float | None = None) -> None:
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    run.font.color.rgb = RGBColor(0, 0, 0)
    if all_caps:
        run.font.all_caps = True
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(_qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
        rFonts.set(_qn(f"w:{attr}"), "Times New Roman")
    if spacing_pt is not None:
        # w:spacing — межсимвольный интервал, единица — 1/20 пункта.
        sp = rPr.find(_qn("w:spacing"))
        if sp is None:
            sp = OxmlElement("w:spacing")
            rPr.append(sp)
        sp.set(_qn("w:val"), str(int(spacing_pt * 20)))


def set_par_format(par, *, alignment=None, first_line_indent_cm: float = 0.0,
                   line_spacing: float = 1.0,
                   space_before: float = 0, space_after: float = 0,
                   left_indent_cm: float | None = None,
                   keep_with_next: bool = False) -> None:
    pf = par.paragraph_format
    if alignment is not None:
        pf.alignment = alignment
    pf.first_line_indent = Cm(first_line_indent_cm)
    if left_indent_cm is not None:
        pf.left_indent = Cm(left_indent_cm)
    pf.line_spacing = line_spacing
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.keep_with_next = keep_with_next


def add_paragraph(doc, text: str = "", *, alignment=None, size: float = 14.0,
                  bold: bool = False, italic: bool = False, underline: bool = False,
                  all_caps: bool = False, spacing_pt: float | None = None,
                  first_line_indent_cm: float = 0.0,
                  line_spacing: float = 1.0,
                  space_before: float = 0, space_after: float = 0,
                  keep_with_next: bool = False):
    """Добавляет параграф с заданными параметрами и возвращает его."""
    p = doc.add_paragraph()
    set_par_format(p, alignment=alignment,
                   first_line_indent_cm=first_line_indent_cm,
                   line_spacing=line_spacing,
                   space_before=space_before, space_after=space_after,
                   keep_with_next=keep_with_next)
    if text:
        r = p.add_run(text)
        set_run_font(r, size=size, bold=bold, italic=italic,
                     underline=underline, all_caps=all_caps,
                     spacing_pt=spacing_pt)
    return p


def set_paragraph_bottom_border(par, *, size: int = 6,
                                color: str = "000000",
                                space: int = 1) -> None:
    pPr = par._element.get_or_add_pPr()
    pBdr = pPr.find(_qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    bottom = pBdr.find(_qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        pBdr.append(bottom)
    bottom.set(_qn("w:val"), "single")
    bottom.set(_qn("w:sz"), str(size))
    bottom.set(_qn("w:space"), str(space))
    bottom.set(_qn("w:color"), color)


def add_page_break(doc):
    p = doc.add_paragraph()
    set_par_format(p, line_spacing=1.0)
    r = p.add_run()
    r.add_break(WD_BREAK.PAGE)
    set_run_font(r, size=1)
    return p


def start_new_page(doc):
    """Создаёт почти-невидимый параграф с pageBreakBefore.

    Используется ПЕРЕД каждой страницей преамбулы (кроме первой), чтобы
    Word/LO начал её с верха новой страницы, не оставляя пустой страницы
    между. В отличие от add_page_break(), не создаёт паразитного пустого
    параграфа в конце предыдущей страницы.
    """
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.page_break_before = True
    pf.line_spacing = 1.0
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.first_line_indent = Cm(0)
    r = p.add_run()
    set_run_font(r, size=1)
    return p


def add_blank(doc, *, size: float = 14.0, space_after: float = 0,
              line_spacing: float = 1.0):
    p = doc.add_paragraph()
    set_par_format(p, line_spacing=line_spacing, space_after=space_after)
    r = p.add_run(" ")
    set_run_font(r, size=size)
    return p


# ----------------------------------------------------------- утилиты таблиц --

def _set_border(parent: OxmlElement, side: str, val: str = "single",
                size: int = 6, color: str = "000000") -> None:
    el = parent.find(_qn(f"w:{side}"))
    if el is None:
        el = OxmlElement(f"w:{side}")
        parent.append(el)
    el.set(_qn("w:val"), val)
    el.set(_qn("w:sz"), str(size))
    el.set(_qn("w:space"), "0")
    el.set(_qn("w:color"), color)


def set_cell_borders(cell, *, top: str = "nil", bottom: str = "nil",
                     left: str = "nil", right: str = "nil",
                     bottom_size: int = 6) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.find(_qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for side, val in (("top", top), ("bottom", bottom),
                      ("left", left), ("right", right)):
        size = bottom_size if side == "bottom" else 6
        _set_border(tcBorders, side, val=val, size=size)


def set_table_no_borders(table) -> None:
    tblPr = table._tbl.find(_qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        table._tbl.insert(0, tblPr)
    tblBorders = tblPr.find(_qn("w:tblBorders"))
    if tblBorders is None:
        tblBorders = OxmlElement("w:tblBorders")
        tblPr.append(tblBorders)
    for side in ("top", "bottom", "left", "right", "insideH", "insideV"):
        _set_border(tblBorders, side, val="nil")


def set_table_all_borders(table, *, size: int = 6) -> None:
    tblPr = table._tbl.find(_qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        table._tbl.insert(0, tblPr)
    tblBorders = tblPr.find(_qn("w:tblBorders"))
    if tblBorders is None:
        tblBorders = OxmlElement("w:tblBorders")
        tblPr.append(tblBorders)
    for side in ("top", "bottom", "left", "right", "insideH", "insideV"):
        _set_border(tblBorders, side, val="single", size=size)


def set_table_layout_fixed(table) -> None:
    tblPr = table._tbl.find(_qn("w:tblPr"))
    if tblPr is None:
        return
    layout = tblPr.find(_qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(_qn("w:type"), "fixed")


def set_cell_width(cell, mm: float) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcW = tcPr.find(_qn("w:tcW"))
    if tcW is None:
        tcW = OxmlElement("w:tcW")
        tcPr.append(tcW)
    twips = int(mm / 25.4 * 1440)
    tcW.set(_qn("w:w"), str(twips))
    tcW.set(_qn("w:type"), "dxa")


def set_grid_widths(table, widths_mm: list[float]) -> None:
    grid = table._tbl.find(_qn("w:tblGrid"))
    if grid is None:
        grid = OxmlElement("w:tblGrid")
        table._tbl.insert(0, grid)
    for el in list(grid):
        grid.remove(el)
    for w in widths_mm:
        col = OxmlElement("w:gridCol")
        col.set(_qn("w:w"), str(int(w / 25.4 * 1440)))
        grid.append(col)


def fill_cell(cell, *, text: str = "", lines: list[str] | None = None,
              alignment=WD_ALIGN_PARAGRAPH.LEFT,
              size: float = 12.0, bold: bool = False, italic: bool = False,
              underline: bool = False, all_caps: bool = False,
              line_spacing: float = 1.0,
              vertical: str = "center",
              first_line_indent_cm: float = 0.0) -> None:
    cell.vertical_alignment = {
        "top": WD_ALIGN_VERTICAL.TOP,
        "center": WD_ALIGN_VERTICAL.CENTER,
        "bottom": WD_ALIGN_VERTICAL.BOTTOM,
    }[vertical]
    for p in list(cell.paragraphs):
        p._element.getparent().remove(p._element)
    seq = lines if lines is not None else [text]
    for s in seq:
        p = cell.add_paragraph()
        set_par_format(p, alignment=alignment,
                       first_line_indent_cm=first_line_indent_cm,
                       line_spacing=line_spacing)
        r = p.add_run(s)
        set_run_font(r, size=size, bold=bold, italic=italic,
                     underline=underline, all_caps=all_caps)


# -------------------------------------------------------------- шапка ВУЗа --

def add_university_header(doc, *, with_logo: bool = False) -> None:
    """Добавляет таблицу-шапку с логотипом или без и финальную двойную линию."""
    if with_logo:
        table = doc.add_table(rows=1, cols=2)
        set_table_no_borders(table)
        set_table_layout_fixed(table)
        set_grid_widths(table, [27, 138])
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        logo_cell, text_cell = table.rows[0].cells
        set_cell_width(logo_cell, 27)
        set_cell_width(text_cell, 138)

        for p in list(logo_cell.paragraphs):
            p._element.getparent().remove(p._element)
        lp = logo_cell.add_paragraph()
        set_par_format(lp, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        if LOGO.exists():
            run = lp.add_run()
            run.add_picture(str(LOGO), width=Mm(22))
        else:
            r = lp.add_run("[герб]")
            set_run_font(r, size=10)
        logo_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        for p in list(text_cell.paragraphs):
            p._element.getparent().remove(p._element)
        for i, line in enumerate(UNIVERSITY_HEADER_LINES):
            p = text_cell.add_paragraph()
            set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                           line_spacing=1.0)
            r = p.add_run(line)
            set_run_font(r, size=11, bold=True)
        text_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    else:
        for line in UNIVERSITY_HEADER_LINES:
            add_paragraph(doc, line, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                          size=10, bold=True, line_spacing=0.95)

    # Двойная линия под шапкой (через параграф с двойным нижним бордюром).
    p = doc.add_paragraph()
    set_par_format(p, line_spacing=1.0, space_after=2)
    r = p.add_run(" ")
    set_run_font(r, size=1)
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    pPr.append(pBdr)
    bottom = OxmlElement("w:bottom")
    bottom.set(_qn("w:val"), "double")
    bottom.set(_qn("w:sz"), "6")
    bottom.set(_qn("w:space"), "1")
    bottom.set(_qn("w:color"), "000000")
    pBdr.append(bottom)


# ------------------------------------------------------------ стр. 1 — титул --

def build_title_page(doc) -> None:
    add_university_header(doc, with_logo=True)

    # Блок «ФАКУЛЬТЕТ / КАФЕДРА» с подчёркнутыми линиями.
    table = doc.add_table(rows=2, cols=2)
    set_table_no_borders(table)
    set_table_layout_fixed(table)
    set_grid_widths(table, [32, 133])

    rows_data = [
        ("ФАКУЛЬТЕТ", FACULTY),
        ("КАФЕДРА", DEPARTMENT_FULL),
    ]
    for row_idx, (label, value) in enumerate(rows_data):
        lc, vc = table.rows[row_idx].cells
        set_cell_width(lc, 32)
        set_cell_width(vc, 133)
        set_cell_borders(lc)
        set_cell_borders(vc, bottom="single")
        fill_cell(lc, text=label, size=11, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="bottom")
        fill_cell(vc, text=value, size=11, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="bottom")

    add_blank(doc, size=14, space_after=24)

    add_paragraph(doc, "РАСЧЕТНО-ПОЯСНИТЕЛЬНАЯ ЗАПИСКА",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=22, bold=True, line_spacing=1.0, space_after=18)
    add_paragraph(doc, "К  КУРСОВОМУ  ПРОЕКТУ",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=18, italic=True, line_spacing=1.0, space_after=18)
    add_paragraph(doc, "НА ТЕМУ:",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=18, italic=True, line_spacing=1.0, space_after=24)

    p = add_paragraph(doc, THEME, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                      size=14, bold=True, line_spacing=1.0, space_after=8)
    set_paragraph_bottom_border(p)

    for _ in range(4):
        p = doc.add_paragraph()
        set_par_format(p, line_spacing=1.0, space_after=8)
        r = p.add_run(" ")
        set_run_font(r, size=14)
        set_paragraph_bottom_border(p)

    add_blank(doc, size=14, space_after=24)

    # Блок подписей: студент / руководитель / консультант. 4×3 без границ,
    # отдельные ячейки получают нижний бордюр там, где идут «подчёркнутые»
    # области ввода.
    sig = doc.add_table(rows=3, cols=4)
    set_table_no_borders(table)
    set_table_layout_fixed(sig)
    set_grid_widths(sig, [45, 35, 45, 40])

    sig_rows = [
        (
            "Студент",
            [("ИУ5-42Б", "(группа)")],
            ("", "(подпись, дата)"),
            (STUDENT_SHORT.replace("Воробьёв Е. А.", "Воробьёв Е. А."),
             "(И. О. Фамилия)"),
        ),
        (
            "Руководитель курсового\nпроекта",
            [(" ", "")],
            ("", "(подпись, дата)"),
            ("", "(И. О. Фамилия)"),
        ),
        (
            "Консультант",
            [(" ", "")],
            ("", "(подпись, дата)"),
            ("", "(И. О. Фамилия)"),
        ),
    ]
    for row_idx, (lbl, group_block, sign_block, name_block) in enumerate(sig_rows):
        cells = sig.rows[row_idx].cells
        set_cell_width(cells[0], 45)
        set_cell_width(cells[1], 35)
        set_cell_width(cells[2], 45)
        set_cell_width(cells[3], 40)
        for c in cells:
            set_cell_borders(c)

        fill_cell(cells[0], lines=lbl.split("\n"),
                  size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                  vertical="top", line_spacing=1.15)

        # Колонка «группа» (или пусто).
        value, hint = group_block[0]
        cells[1].vertical_alignment = WD_ALIGN_VERTICAL.TOP
        for p in list(cells[1].paragraphs):
            p._element.getparent().remove(p._element)
        p_val = cells[1].add_paragraph()
        set_par_format(p_val, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r_val = p_val.add_run(value)
        set_run_font(r_val, size=12)
        set_paragraph_bottom_border(p_val)
        p_hint = cells[1].add_paragraph()
        set_par_format(p_hint, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r_hint = p_hint.add_run(hint)
        set_run_font(r_hint, size=10)

        # Подпись/дата.
        cells[2].vertical_alignment = WD_ALIGN_VERTICAL.TOP
        for p in list(cells[2].paragraphs):
            p._element.getparent().remove(p._element)
        p_val = cells[2].add_paragraph()
        set_par_format(p_val, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r_val = p_val.add_run(sign_block[0])
        set_run_font(r_val, size=12)
        set_paragraph_bottom_border(p_val)
        p_hint = cells[2].add_paragraph()
        set_par_format(p_hint, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r_hint = p_hint.add_run(sign_block[1])
        set_run_font(r_hint, size=10)

        # И. О. Фамилия.
        cells[3].vertical_alignment = WD_ALIGN_VERTICAL.TOP
        for p in list(cells[3].paragraphs):
            p._element.getparent().remove(p._element)
        p_val = cells[3].add_paragraph()
        set_par_format(p_val, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r_val = p_val.add_run(name_block[0])
        set_run_font(r_val, size=12)
        set_paragraph_bottom_border(p_val)
        p_hint = cells[3].add_paragraph()
        set_par_format(p_hint, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r_hint = p_hint.add_run(name_block[1])
        set_run_font(r_hint, size=10)

    add_blank(doc, size=14, space_after=24)
    add_paragraph(doc, f"{YEAR} г.",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=14, italic=True, line_spacing=1.0)


# ----------------------------------------------------------- стр. 2 — задание --

def build_assignment_page(doc) -> None:
    add_university_header(doc, with_logo=False)

    # «УТВЕРЖДАЮ» + блок заведующего кафедрой (правый верх).
    table = doc.add_table(rows=1, cols=2)
    set_table_no_borders(table)
    set_table_layout_fixed(table)
    set_grid_widths(table, [80, 85])

    left, right = table.rows[0].cells
    set_cell_width(left, 80)
    set_cell_width(right, 85)
    for c in (left, right):
        set_cell_borders(c)
    fill_cell(left, text="", size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT)

    right.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    for p in list(right.paragraphs):
        p._element.getparent().remove(p._element)
    p = right.add_paragraph()
    set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.0,
                   space_after=0)
    r = p.add_run("УТВЕРЖДАЮ")
    set_run_font(r, size=11, bold=True)

    # Под-таблица 2×2: «Заведующий кафедрой» + индекс / Фамилия + подпись.
    sub = right.add_table(rows=3, cols=2)
    set_table_no_borders(sub)
    set_table_layout_fixed(sub)
    set_grid_widths(sub, [50, 35])
    sub_rows = [
        ("Заведующий кафедрой", (DEPT_INDEX, "(индекс)")),
        ("",                     (HEAD_OF_DEPARTMENT, "(И. О. Фамилия)")),
        ("",                     ("",                  "(подпись, дата)")),
    ]
    for i, (lbl, (val, hint)) in enumerate(sub_rows):
        lc, vc = sub.rows[i].cells
        set_cell_width(lc, 50)
        set_cell_width(vc, 35)
        for c in (lc, vc):
            set_cell_borders(c)
        fill_cell(lc, text=lbl, size=10, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                  vertical="top", line_spacing=0.95)
        vc.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        for p in list(vc.paragraphs):
            p._element.getparent().remove(p._element)
        p_val = vc.add_paragraph()
        set_par_format(p_val, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=0.95, space_after=0)
        r_val = p_val.add_run(val)
        set_run_font(r_val, size=10)
        set_paragraph_bottom_border(p_val)
        p_hint = vc.add_paragraph()
        set_par_format(p_hint, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=0.95, space_after=0)
        r_hint = p_hint.add_run(hint)
        set_run_font(r_hint, size=9)

    add_paragraph(doc, "З А Д А Н И Е",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=16, bold=True, line_spacing=1.0,
                  space_before=2, space_after=0,
                  spacing_pt=None)
    add_paragraph(doc, "на выполнение курсовой работы",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=13, bold=True, line_spacing=1.0,
                  space_after=6)

    # Поля «по дисциплине / Студент группы / Тема / Направленность / Источник».
    fields_label_value = [
        ("по дисциплине", DISCIPLINE),
        ("Студент группы", f"{GROUP}    {STUDENT_FULL}"),
        ("Тема курсовой работы", THEME),
    ]
    for label, value in fields_label_value:
        _add_label_value_row(doc, label, value, label_mm=45, value_mm=120)
        if label == "Студент группы":
            # Подпись (Фамилия, имя, отчество) под значением.
            _add_caption_row(doc, "", "(Фамилия, имя, отчество)",
                             label_mm=45, value_mm=120)

    _add_label_value_row(
        doc,
        "Направленность КР (учебная, исследовательская, практическая, др.)",
        "УЧЕБНАЯ",
        label_mm=110, value_mm=55,
    )
    _add_label_value_row(
        doc,
        "Источник тематики (кафедра, предприятие, НИР)",
        "КАФЕДРА",
        label_mm=100, value_mm=65,
    )

    add_paragraph(doc, "Задание:",
                  alignment=WD_ALIGN_PARAGRAPH.LEFT,
                  size=11, bold=True, line_spacing=1.0,
                  space_before=2, space_after=1)
    for item in ASSIGNMENT_ITEMS:
        p = doc.add_paragraph()
        set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       line_spacing=0.95, first_line_indent_cm=0.0,
                       space_after=0)
        r = p.add_run(item)
        set_run_font(r, size=10)
        set_paragraph_bottom_border(p)

    add_paragraph(doc, "Оформление курсовой работы:",
                  alignment=WD_ALIGN_PARAGRAPH.LEFT,
                  size=11, bold=True, line_spacing=1.0,
                  space_before=2, space_after=1)
    p = doc.add_paragraph()
    set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.0,
                   space_after=1)
    r1 = p.add_run("Расчётно-пояснительная записка (Отчёт по КР) на ")
    set_run_font(r1, size=11)
    r2 = p.add_run(f"  {RPZ_PAGES}  ")
    set_run_font(r2, size=11, underline=True)
    r3 = p.add_run(" листах формата А4.")
    set_run_font(r3, size=11)

    p = doc.add_paragraph()
    set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.0,
                   space_after=1)
    r = p.add_run("Перечень графического (иллюстративного) материала "
                  "(чертежи, плакаты, слайды и т.п.)")
    set_run_font(r, size=11)
    set_paragraph_bottom_border(p)

    for sheet in GRAPHIC_SHEETS:
        p = doc.add_paragraph()
        set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                       line_spacing=0.95, space_after=0)
        r = p.add_run(sheet)
        set_run_font(r, size=10)
        set_paragraph_bottom_border(p)

    p = doc.add_paragraph()
    set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.0,
                   space_before=4, space_after=2)
    r1 = p.add_run("Дата выдачи задания  «")
    set_run_font(r1, size=11)
    r2 = p.add_run(f" {ISSUE_DATE_DAY} ")
    set_run_font(r2, size=11, underline=True)
    r3 = p.add_run("»  ")
    set_run_font(r3, size=11)
    r4 = p.add_run(f" {ISSUE_DATE_MONTH} ")
    set_run_font(r4, size=11, underline=True)
    r5 = p.add_run(f"   {YEAR} г.")
    set_run_font(r5, size=11)

    _add_signature_row_assignment(doc, "Руководитель курсовой работы")
    _add_signature_row_assignment(doc, "Студент")

    p = doc.add_paragraph()
    set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, line_spacing=1.0,
                   space_before=4)
    r1 = p.add_run("Примечание: ")
    set_run_font(r1, size=10, underline=True)
    r2 = p.add_run("Задание оформляется в двух экземплярах: один выдаётся "
                   "студенту, второй хранится на кафедре.")
    set_run_font(r2, size=10)


def _add_label_value_row(doc, label: str, value: str,
                         label_mm: float, value_mm: float,
                         multi_line_label: bool = False) -> None:
    table = doc.add_table(rows=1, cols=2)
    set_table_no_borders(table)
    set_table_layout_fixed(table)
    set_grid_widths(table, [label_mm, value_mm])
    lc, vc = table.rows[0].cells
    set_cell_width(lc, label_mm)
    set_cell_width(vc, value_mm)
    set_cell_borders(lc)
    set_cell_borders(vc, bottom="single")
    fill_cell(lc, text=label, size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT,
              vertical="bottom")
    fill_cell(vc, text=value, size=12,
              alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="bottom",
              first_line_indent_cm=0.2)


def _add_caption_row(doc, label: str, hint: str,
                     label_mm: float, value_mm: float) -> None:
    table = doc.add_table(rows=1, cols=2)
    set_table_no_borders(table)
    set_table_layout_fixed(table)
    set_grid_widths(table, [label_mm, value_mm])
    lc, vc = table.rows[0].cells
    set_cell_width(lc, label_mm)
    set_cell_width(vc, value_mm)
    set_cell_borders(lc)
    set_cell_borders(vc)
    fill_cell(lc, text=label, size=10, alignment=WD_ALIGN_PARAGRAPH.LEFT)
    fill_cell(vc, text=hint, size=10,
              alignment=WD_ALIGN_PARAGRAPH.CENTER)


def _add_signature_row_assignment(doc, label: str) -> None:
    table = doc.add_table(rows=2, cols=3)
    set_table_no_borders(table)
    set_table_layout_fixed(table)
    set_grid_widths(table, [70, 50, 45])
    cells_top = table.rows[0].cells
    cells_bot = table.rows[1].cells
    for c in list(cells_top) + list(cells_bot):
        set_cell_borders(c)
        set_cell_width(c, 70 if c is cells_top[0] or c is cells_bot[0]
                       else 50 if c is cells_top[1] or c is cells_bot[1]
                       else 45)
    cells_top[1].vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
    cells_top[2].vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
    set_cell_borders(cells_top[1], bottom="single")
    set_cell_borders(cells_top[2], bottom="single")

    fill_cell(cells_top[0], text=label, size=12,
              alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="bottom")
    fill_cell(cells_top[1], text="", size=12, vertical="bottom")
    fill_cell(cells_top[2], text="", size=12, vertical="bottom")

    fill_cell(cells_bot[0], text="", size=10)
    fill_cell(cells_bot[1], text="(подпись, дата)",
              size=10, alignment=WD_ALIGN_PARAGRAPH.CENTER)
    fill_cell(cells_bot[2], text="(И. О. Фамилия)",
              size=10, alignment=WD_ALIGN_PARAGRAPH.CENTER)


# ----------------------------------------------------- стр. 3 — календарный --

def build_calendar_page(doc) -> None:
    add_university_header(doc, with_logo=False)

    add_blank(doc, size=14, space_after=12)
    add_paragraph(doc, "КАЛЕНДАРНЫЙ ПЛАН",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=18, bold=True, line_spacing=1.0, space_after=4)
    add_paragraph(doc, "на выполнение курсовой работы",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=16, bold=True, line_spacing=1.0, space_after=18)

    _add_label_value_row(doc, "по дисциплине", DISCIPLINE,
                         label_mm=45, value_mm=120)
    _add_label_value_row(doc, "Студент группы", f"{GROUP}    {STUDENT_FULL}",
                         label_mm=45, value_mm=120)
    _add_caption_row(doc, "", "(Фамилия, имя, отчество)",
                     label_mm=45, value_mm=120)
    _add_label_value_row(doc, "Тема курсовой работы", THEME,
                         label_mm=45, value_mm=120)
    add_blank(doc, size=14, space_after=6)

    # Таблица календарного плана: 6 колонок (№, наименование, план, факт,
    # руководитель, куратор) с двухстрочной шапкой.
    table = doc.add_table(rows=2 + len(CALENDAR_ROWS), cols=6)
    set_table_all_borders(table)
    set_table_layout_fixed(table)
    widths = [10, 63, 23, 17, 32, 20]
    set_grid_widths(table, widths)

    # Объединения шапки: №, Наименование — на 2 строки; «Сроки выполнения
    # этапов» — на 2 колонки; «Отметка о выполнении» — на 2 колонки.
    header_row1 = table.rows[0].cells
    header_row2 = table.rows[1].cells

    for c, mm in zip(header_row1, widths):
        set_cell_width(c, mm)
    for c, mm in zip(header_row2, widths):
        set_cell_width(c, mm)

    # Объединить ячейки шапки.
    header_row1[0].merge(header_row2[0])
    header_row1[1].merge(header_row2[1])
    header_row1[2].merge(header_row1[3])
    header_row1[4].merge(header_row1[5])

    fill_cell(header_row1[0], text="№\nп/п", size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row1[1],
              lines=["Наименование этапов",
                     "выпускной квалификационной работы"],
              size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row1[2], text="Сроки выполнения этапов",
              size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row1[4], text="Отметка о выполнении",
              size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row2[2], text="план", size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row2[3], text="факт", size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row2[4], text="Руководитель КП",
              size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)
    fill_cell(header_row2[5], text="Куратор",
              size=11, bold=True,
              alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
              line_spacing=1.0)

    # Строки данных.
    for i, (num, name, plan_date) in enumerate(CALENDAR_ROWS, start=2):
        cells = table.rows[i].cells
        for c, mm in zip(cells, widths):
            set_cell_width(c, mm)
        fill_cell(cells[0], text=num, size=12,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, vertical="center",
                  line_spacing=1.0)
        fill_cell(cells[1], lines=name.split("\n"), size=12,
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="center",
                  line_spacing=1.15)
        # «План» — дата сверху, под ней мелким курсивом — пояснение.
        cells[2].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in list(cells[2].paragraphs):
            p._element.getparent().remove(p._element)
        p1 = cells[2].add_paragraph()
        set_par_format(p1, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r1 = p1.add_run(plan_date)
        set_run_font(r1, size=12)
        p2 = cells[2].add_paragraph()
        set_par_format(p2, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                       line_spacing=1.0)
        r2 = p2.add_run("Планируемая дата")
        set_run_font(r2, size=9, italic=True)
        fill_cell(cells[3], text="", size=12)
        fill_cell(cells[4], text="", size=12)
        fill_cell(cells[5], text="", size=12)

    add_blank(doc, size=12, space_after=18)
    # Подписи внизу страницы.
    sign = doc.add_table(rows=2, cols=4)
    set_table_no_borders(sign)
    set_table_layout_fixed(sign)
    sign_widths = [22, 53, 45, 45]
    set_grid_widths(sign, sign_widths)
    sr_top = sign.rows[0].cells
    sr_bot = sign.rows[1].cells
    for c, w in zip(sr_top, sign_widths):
        set_cell_width(c, w)
        set_cell_borders(c)
    for c, w in zip(sr_bot, sign_widths):
        set_cell_width(c, w)
        set_cell_borders(c)
    set_cell_borders(sr_top[1], bottom="single")
    set_cell_borders(sr_top[3], bottom="single")

    fill_cell(sr_top[0], text="Студент", size=12,
              alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="bottom")
    fill_cell(sr_top[1], text="", size=12, vertical="bottom")
    fill_cell(sr_top[2], text="Руководитель работы", size=12,
              alignment=WD_ALIGN_PARAGRAPH.LEFT, vertical="bottom")
    fill_cell(sr_top[3], text="", size=12, vertical="bottom")
    fill_cell(sr_bot[0], text="", size=10)
    fill_cell(sr_bot[1], text="(подпись, дата)",
              size=10, alignment=WD_ALIGN_PARAGRAPH.CENTER)
    fill_cell(sr_bot[2], text="", size=10)
    fill_cell(sr_bot[3], text="(подпись, дата)",
              size=10, alignment=WD_ALIGN_PARAGRAPH.CENTER)


# ---------------------------------------------------- стр. 4 — аннотация --

def build_annotation_page(doc) -> None:
    add_paragraph(doc, "АННОТАЦИЯ",
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  size=14, bold=True, line_spacing=1.5,
                  space_before=0, space_after=18)
    for text in ANNOTATION_PARAGRAPHS:
        p = doc.add_paragraph()
        set_par_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       line_spacing=1.5, first_line_indent_cm=1.25,
                       space_after=0)
        r = p.add_run(text)
        set_run_font(r, size=14)


# ------------------------------------------------------------- сборка --------

def find_marker_paragraph(doc):
    for para in doc.paragraphs:
        if MARKER in para.text:
            return para
    return None


def find_toc_marker_paragraph(doc):
    for para in doc.paragraphs:
        if TOC_MARKER in para.text:
            return para
    return None


# Имена H1, которые нужно ИСКЛЮЧИТЬ из оглавления, потому что они
# относятся к преамбуле, а не к основному корпусу РПЗ (само СОДЕРЖАНИЕ
# и АННОТАЦИЯ оказываются перед основным телом и не нумеруются).
_TOC_SKIP = {"СОДЕРЖАНИЕ", "АННОТАЦИЯ"}


def _heading_label(text: str) -> str:
    """Возвращает текст заголовка для оглавления в естественной форме."""
    return " ".join(text.split())


def replace_toc_placeholder(doc) -> None:
    """Собирает статический TOC из всех Heading 1 после маркера и
    подставляет вместо маркера TOC."""
    toc_para = find_toc_marker_paragraph(doc)
    if toc_para is None:
        return

    # Собираем заголовки в порядке их появления в документе, но только
    # ПОСЛЕ маркера TOC (чтобы СОДЕРЖАНИЕ-заголовок не попал в сам TOC).
    body = doc.element.body
    toc_el = toc_para._element
    headings: list[str] = []
    seen_marker = False
    for child in body.iterchildren():
        if child is toc_el:
            seen_marker = True
            continue
        if not seen_marker:
            continue
        if child.tag != _qn("w:p"):
            continue
        pPr = child.find(_qn("w:pPr"))
        if pPr is None:
            continue
        pStyle = pPr.find(_qn("w:pStyle"))
        if pStyle is None:
            continue
        style_val = pStyle.get(_qn("w:val"), "")
        if style_val not in ("Heading1", "1", "Heading 1"):
            continue
        text = "".join(t.text or "" for t in child.iter(_qn("w:t"))).strip()
        if not text or text.upper() in _TOC_SKIP:
            continue
        headings.append(_heading_label(text))

    # Строим список параграфов оглавления через таблицу 1×2 без рамок
    # с табуляторами под точки и право-выровненными номерами страниц-заглушками.
    # Номера страниц проставлять статически нельзя (мы не знаем разбиение
    # после нашей же подстановки), поэтому в начальной сборке используем
    # пустые номера; обновятся в шаге 2 (см. fill_toc_page_numbers).
    new_elements = []
    for title in headings:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.line_spacing = 1.5
        pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        pf.first_line_indent = Cm(0)
        pf.space_after = Pt(0)
        # Tab stop: лидер из точек до 158 мм, правый край — для номера.
        from docx.shared import Mm as _Mm
        from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
        pf.tab_stops.add_tab_stop(
            _Mm(158), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

        r = p.add_run(title)
        set_run_font(r, size=14)
        r_tab = p.add_run("\t")
        set_run_font(r_tab, size=14)
        # Метка-плейсхолдер для номера страницы, чтобы потом подменить
        # её на реальное число (см. fill_toc_page_numbers).
        r_num = p.add_run(f"__PG__{title}__")
        set_run_font(r_num, size=14)
        new_elements.append(p._element)

    # Перемещаем сформированные параграфы перед маркером TOC.
    for el in new_elements:
        toc_el.addprevious(el)
    # Удаляем сам маркер.
    toc_el.getparent().remove(toc_el)


def assemble(target_path: Path) -> None:
    doc = Document(str(target_path))
    marker = find_marker_paragraph(doc)
    if marker is None:
        raise SystemExit(
            f"Маркер {MARKER!r} не найден в {target_path}. "
            "Проверьте, что docs/00_Преамбула.md содержит плейсхолдер."
        )

    body = doc.element.body
    count_before = len(list(body))

    build_title_page(doc)
    start_new_page(doc)
    build_assignment_page(doc)
    start_new_page(doc)
    build_calendar_page(doc)
    start_new_page(doc)
    build_annotation_page(doc)
    # Следующий блок документа — H1 «СОДЕРЖАНИЕ», у которого
    # уже выставлен pageBreakBefore через стиль Heading 1.

    # CT_Body вставляет каждый p/tbl перед последним sectPr. Значит новые
    # элементы заняли позиции [count_before-1 ... -1], а sectPr сдвинулся
    # в самый конец. Берём их в исходном порядке и переносим перед маркером.
    all_now = list(body)
    new_in_order = [
        el for el in all_now[count_before - 1:-1]
        if el.tag != _qn("w:sectPr")
    ]

    marker_el = marker._element
    for el in new_in_order:
        marker_el.addprevious(el)

    marker_el.getparent().remove(marker_el)

    # Преамбула уже на месте, теперь заменим маркер TOC на статическое
    # оглавление из всех H1 основного корпуса.
    replace_toc_placeholder(doc)

    doc.save(str(target_path))
    print(f"✓ Преамбула вставлена: {target_path.name} "
          f"(+{len(new_in_order)} элементов)")


def main() -> None:
    target = (
        Path(sys.argv[1]) if len(sys.argv) > 1
        else ROOT / "build" / "Воробьёв_РПЗ.docx"
    )
    assemble(target.resolve())


if __name__ == "__main__":
    main()
