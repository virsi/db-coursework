"""Генерация reference.docx для pandoc с оформлением по ГОСТ 7.32-2017.

Ключевые требования ГОСТ 7.32-2017:

* Размер шрифта: 14 pt (для основного текста). Times New Roman, чёрный.
* Межстрочный интервал: 1.5.
* Поля страницы: левое 30 мм, правое 15 мм, верхнее 20 мм, нижнее 20 мм.
* Абзацный отступ: 1.25 см, выравнивание по ширине.
* Заголовки разделов: 14 pt полужирные, выравнивание по центру (для H1
  ПРОПИСНЫМИ), без точки в конце, без подчёркивания, отбивка пустой
  строкой; каждый раздел — с новой страницы.
* Подзаголовки (1.1, 1.2 …) — 14 pt полужирные обычным регистром,
  выравнивание слева (с абзацного отступа).
* Подписи рисунков (под рисунком): «Рисунок N — Название», по центру.
* Подписи таблиц (над таблицей): «Таблица N — Название», слева без
  абзацного отступа.
* Внутри таблиц — TNR 12 pt, одинарный интервал, без первой строки.
* Нумерация страниц — внизу по центру, начиная со 2-й страницы.

Запуск:
    arch -arm64 .venv/bin/python tools/build_reference_docx.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

BLACK = RGBColor(0, 0, 0)

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "tools" / "reference.docx"
SOURCE_DEFAULT = "/tmp/_pandoc_reference_seed.docx"


def fetch_pandoc_default() -> str:
    """Получить дефолтный reference.docx от pandoc."""
    with open(SOURCE_DEFAULT, "wb") as fh:
        subprocess.run(
            ["pandoc", "--print-default-data-file", "reference.docx"],
            check=True, stdout=fh,
        )
    return SOURCE_DEFAULT


def set_section_margins(doc: Document) -> None:
    """Установить поля по ГОСТ 7.32-2017: 30/15/20/20 мм."""
    for section in doc.sections:
        section.left_margin   = Mm(30)
        section.right_margin  = Mm(15)
        section.top_margin    = Mm(20)
        section.bottom_margin = Mm(20)
        # Заголовки и колонтитулы — стандартные смещения.
        section.header_distance = Mm(10)
        section.footer_distance = Mm(10)


def _force_rfonts(element, name: str = "Times New Roman") -> None:
    """Принудительно зафиксировать шрифт для ascii/hAnsi/cs/eastAsia."""
    rPr = element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
        rFonts.set(qn(f"w:{attr}"), name)


def set_run_font(run, *, name: str = "Times New Roman", size: int = 14,
                 bold: bool | None = None) -> None:
    run.font.name = name
    _force_rfonts(run._element, name=name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def configure_style(doc: Document, name: str, *, font_size: int,
                    bold: bool = False, italic: bool = False,
                    all_caps: bool = False,
                    space_before: int = 0, space_after: int = 0,
                    line_spacing: float = 1.5,
                    first_line_indent: float | None = None,
                    alignment=None,
                    page_break_before: bool = False,
                    keep_with_next: bool | None = None) -> None:
    style = doc.styles[name]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(font_size)
    font.bold = bold
    font.italic = italic
    font.color.rgb = BLACK
    if all_caps:
        font.all_caps = True

    pf = style.paragraph_format
    if alignment is not None:
        pf.alignment = alignment
    pf.line_spacing = line_spacing
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if first_line_indent is not None:
        pf.first_line_indent = Cm(first_line_indent)
    if keep_with_next is not None:
        pf.keep_with_next = keep_with_next
    elif "Heading" in name:
        pf.keep_with_next = True
    if page_break_before:
        pf.page_break_before = True

    _force_rfonts(style.element)


def add_page_numbers(doc: Document) -> None:
    """Вставить нумерацию страниц снизу по центру (поле PAGE)."""
    for section in doc.sections:
        footer = section.footer
        for para in list(footer.paragraphs):
            para.clear()
        para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run = para.add_run()
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), "PAGE   \\* MERGEFORMAT")
        nested_run = OxmlElement("w:r")
        nested_text = OxmlElement("w:t")
        nested_text.text = "1"
        nested_run.append(nested_text)
        fld.append(nested_run)
        run._element.append(fld)
        set_run_font(run, size=14)


def patch_doc_defaults(docx_path: Path) -> None:
    """Перезаписать docDefaults в word/styles.xml: TNR 14pt по умолчанию,
    межстрочный 1.5, выравнивание по ширине."""
    tmp = docx_path.with_suffix(".docx.patchtmp")
    with zipfile.ZipFile(docx_path, "r") as src, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.namelist():
            data = src.read(item)
            if item == "word/styles.xml":
                text = data.decode("utf-8")
                new_default = (
                    '<w:docDefaults>'
                    '<w:rPrDefault><w:rPr>'
                    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
                    'w:cs="Times New Roman" w:eastAsia="Times New Roman"/>'
                    '<w:sz w:val="28"/><w:szCs w:val="28"/>'
                    '<w:lang w:val="ru-RU"/>'
                    '</w:rPr></w:rPrDefault>'
                    '<w:pPrDefault><w:pPr>'
                    # line=360 (twentieths) = 18pt = ~1.5 от 12pt-кегля;
                    # для 14pt-кегля линия 1.5 — это 360 twips, line-rule=auto.
                    '<w:spacing w:after="0" w:before="0" '
                    'w:line="360" w:lineRule="auto"/>'
                    '<w:jc w:val="both"/>'
                    '<w:ind w:firstLine="709"/>'  # 709 twips = 1.25 cm
                    '</w:pPr></w:pPrDefault>'
                    '</w:docDefaults>'
                )
                text = re.sub(r"<w:docDefaults>.*?</w:docDefaults>",
                              new_default, text, count=1, flags=re.DOTALL)
                data = text.encode("utf-8")
            dst.writestr(item, data)
    shutil.move(tmp, docx_path)


def _setup_table_style(doc: Document, style_name: str) -> None:
    """Унифицированная настройка табличного стиля по ГОСТу.

    Внутри ячеек: TNR 12 pt, одинарный интервал, без первой строки,
    выравнивание слева. Границы single 4 единицы (0.5 pt) чёрные.
    """
    if style_name not in doc.styles:
        doc.styles.add_style(style_name, WD_STYLE_TYPE.TABLE)
    ts = doc.styles[style_name]
    ts.font.name = "Times New Roman"
    ts.font.size = Pt(12)
    ts.font.color.rgb = BLACK
    pf = ts.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.0
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT

    _force_rfonts(ts.element)

    tblPr = ts.element.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        ts.element.insert(0, tblPr)
    tblBorders = tblPr.find(qn("w:tblBorders"))
    if tblBorders is None:
        tblBorders = OxmlElement("w:tblBorders")
        tblPr.append(tblBorders)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        old = tblBorders.find(qn(f"w:{side}"))
        if old is not None:
            tblBorders.remove(old)
        tblBorders.append(el)

    # Автоматический режим раскладки колонок — даёт Word'у право
    # перераспределять ширины под содержимое (вместе с tblW=100%).
    tblLayout = OxmlElement("w:tblLayout")
    tblLayout.set(qn("w:type"), "autofit")
    old = tblPr.find(qn("w:tblLayout"))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(tblLayout)

    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), "5000")    # 5000 / 50 = 100%
    tblW.set(qn("w:type"), "pct")
    old = tblPr.find(qn("w:tblW"))
    if old is not None:
        tblPr.remove(old)
    tblPr.insert(0, tblW)


def main() -> None:
    src = fetch_pandoc_default()
    shutil.copy(src, TARGET)

    doc = Document(str(TARGET))

    set_section_margins(doc)

    # Базовый Normal — TNR 14 pt, межстрочный 1.5, justify, отступ 1.25 см.
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal.font.color.rgb = BLACK
    pf = normal.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.line_spacing = 1.5
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.first_line_indent = Cm(1.25)
    pf.space_after = Pt(0)
    pf.space_before = Pt(0)
    _force_rfonts(normal.element)

    # H1 — ПРОПИСНЫМИ полужирно, по центру, КАЖДЫЙ С НОВОЙ СТРАНИЦЫ
    # (требование ГОСТ 7.32 — раздел начинается с новой страницы).
    # Это автоматически обеспечивает разрыв перед каждым крупным
    # разделом: «СОДЕРЖАНИЕ», «Введение», нумерованные разделы 2–18,
    # «Заключение», «Список использованной литературы», «ПРИЛОЖЕНИЕ ...».
    configure_style(doc, "Heading 1",
                    font_size=14, bold=True, all_caps=True,
                    space_before=0, space_after=18,
                    line_spacing=1.5,
                    first_line_indent=0,
                    alignment=WD_ALIGN_PARAGRAPH.CENTER,
                    page_break_before=True,
                    keep_with_next=True)

    # H2 (1.1) — TNR 14 pt полужирно, обычный регистр, слева с абзаца.
    configure_style(doc, "Heading 2",
                    font_size=14, bold=True,
                    space_before=12, space_after=12,
                    line_spacing=1.5,
                    first_line_indent=1.25,
                    alignment=WD_ALIGN_PARAGRAPH.LEFT,
                    keep_with_next=True)

    # H3 (1.1.1) — TNR 14 pt полужирно курсивом, слева с абзаца.
    configure_style(doc, "Heading 3",
                    font_size=14, bold=True, italic=True,
                    space_before=10, space_after=10,
                    line_spacing=1.5,
                    first_line_indent=1.25,
                    alignment=WD_ALIGN_PARAGRAPH.LEFT,
                    keep_with_next=True)

    configure_style(doc, "Heading 4",
                    font_size=14, bold=False, italic=True,
                    space_before=8, space_after=8,
                    line_spacing=1.5,
                    first_line_indent=1.25,
                    alignment=WD_ALIGN_PARAGRAPH.LEFT)

    # Title (на титульный лист используем custom-стили, см. ниже).
    if "Title" in doc.styles:
        configure_style(doc, "Title",
                        font_size=16, bold=True,
                        space_before=0, space_after=12,
                        line_spacing=1.5,
                        first_line_indent=0,
                        alignment=WD_ALIGN_PARAGRAPH.CENTER)

    # Caption — подпись рисунка/таблицы. TNR 14 pt, обычный, по центру.
    if "Caption" in doc.styles:
        cap = doc.styles["Caption"]
        cap.font.italic = False
        cap.font.bold = False
        cap.font.size = Pt(14)
        cap.font.name = "Times New Roman"
        cap.font.color.rgb = BLACK
        cap_pf = cap.paragraph_format
        cap_pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_pf.first_line_indent = Cm(0)
        cap_pf.line_spacing = 1.5
        cap_pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        cap_pf.space_before = Pt(6)
        cap_pf.space_after = Pt(12)
        cap_pf.keep_with_next = False
        _force_rfonts(cap.element)

    # Кодовые блоки — Courier New 11pt, чёрные, без первой строки.
    for code_style in ("Source Code", "Verbatim Char"):
        if code_style in doc.styles:
            cs = doc.styles[code_style]
            cs.font.name = "Courier New"
            cs.font.size = Pt(11)
            cs.font.color.rgb = BLACK
            if hasattr(cs, "paragraph_format"):
                try:
                    cs.paragraph_format.first_line_indent = Cm(0)
                    cs.paragraph_format.line_spacing = 1.0
                except Exception:
                    pass
            rPr = cs.element.get_or_add_rPr()
            rFonts = rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                rPr.append(rFonts)
            for attr in ("ascii", "hAnsi", "cs"):
                rFonts.set(qn(f"w:{attr}"), "Courier New")

    # Гиперссылки — чёрные без подчёркивания (как в печатном тексте).
    if "Hyperlink" in doc.styles:
        h = doc.styles["Hyperlink"]
        h.font.color.rgb = BLACK
        h.font.underline = False

    # Списки — также с абзацным отступом 1.25 см, justify.
    for list_style in ("List Paragraph", "List Bullet", "List Number"):
        if list_style in doc.styles:
            ls = doc.styles[list_style]
            ls.font.name = "Times New Roman"
            ls.font.size = Pt(14)
            ls.font.color.rgb = BLACK
            lpf = ls.paragraph_format
            lpf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            lpf.line_spacing = 1.5
            lpf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            lpf.space_after = Pt(0)
            lpf.space_before = Pt(0)
            lpf.first_line_indent = Cm(0)
            _force_rfonts(ls.element)

    # Кастомные стили титульного листа. Межстрочный интервал 1.0 для
    # компактности, отбивки задаём через space_before/space_after.
    title_styles = [
        # (name, size, bold, align, line_spacing, space_before, space_after)
        ("TitleCenter", 14, False, WD_ALIGN_PARAGRAPH.CENTER, 1.0, 0, 6),
        ("TitleBold",   14, True,  WD_ALIGN_PARAGRAPH.CENTER, 1.0, 12, 12),
        ("TitleBig",    16, True,  WD_ALIGN_PARAGRAPH.CENTER, 1.0, 0, 8),
        ("SignLine",    14, False, WD_ALIGN_PARAGRAPH.LEFT,   1.0, 0, 10),
    ]
    for (style_name, font_size, bold, alignment,
         ls, sb, sa) in title_styles:
        if style_name in doc.styles:
            st = doc.styles[style_name]
        else:
            st = doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles["Normal"]
        st.font.name = "Times New Roman"
        st.font.size = Pt(font_size)
        st.font.bold = bold
        st.font.color.rgb = BLACK
        spf = st.paragraph_format
        spf.alignment = alignment
        spf.first_line_indent = Cm(0)
        spf.line_spacing = ls
        spf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        spf.space_before = Pt(sb)
        spf.space_after = Pt(sa)
        _force_rfonts(st.element)

    # Табличные стили: применяем единые настройки.
    for ts_name in ("Table", "Table Grid", "Table Normal"):
        _setup_table_style(doc, ts_name)

    add_page_numbers(doc)

    doc.save(str(TARGET))

    patch_doc_defaults(TARGET)

    print(f"✓ Reference docx сохранён: {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
