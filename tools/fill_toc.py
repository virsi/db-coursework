"""Заполнение реальных номеров страниц в оглавлении РПЗ.

Работа в два прохода (см. Makefile):

1. `tools/build_preamble.py` создаёт оглавление из заголовков H1 с
   плейсхолдерами вида `__PG__<заголовок>__` вместо номеров страниц.
2. LibreOffice конвертирует docx → preliminary PDF; в этом PDF
   плейсхолдеры физически отрисованы, но мы по-прежнему знаем, на
   какой странице какой заголовок появляется первый раз.
3. Этот скрипт читает PDF через `pdftotext`, для каждого плейсхолдера
   ищет первое появление соответствующего заголовка и подменяет
   плейсхолдер на число.
4. LibreOffice ещё раз конвертирует обновлённый docx → final PDF.

Запуск:
    arch -arm64 .venv/bin/python tools/fill_toc.py
        build/Воробьёв_РПЗ.docx build/Воробьёв_РПЗ.pdf
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

PLACEHOLDER = re.compile(r"__PG__(.+?)__")


def _norm(text: str) -> str:
    """Удалить переносы строк / лишние пробелы для устойчивого сравнения."""
    return " ".join(text.split())


def pdf_pages_text(pdf_path: Path) -> list[str]:
    """Возвращает список текстов по страницам (по разделителю \\f)."""
    out = subprocess.check_output(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        stderr=subprocess.DEVNULL,
    ).decode("utf-8", errors="ignore")
    return out.split("\f")


def find_first_page(pages: list[str], title: str) -> int | None:
    """Найти 1-based номер страницы, где впервые встречается заголовок.

    Поиск устойчив к переносам строк в PDF: сравниваем нормализованные
    строки (один пробел между токенами). Страницы, содержащие маркер
    `__PG__` (это сами страницы оглавления с ещё незаполненными
    плейсхолдерами), пропускаются — иначе все номера схлопываются в
    номер страницы TOC.
    """
    norm_title = _norm(title).casefold()
    for idx, raw in enumerate(pages, start=1):
        if "__PG__" in raw:
            continue
        if norm_title in _norm(raw).casefold():
            return idx
    return None


def fill(docx_path: Path, pdf_path: Path) -> None:
    pages = pdf_pages_text(pdf_path)
    doc = Document(str(docx_path))

    replaced = 0
    missed = 0

    # Плейсхолдер всегда оказывается в одном `<w:r>` (build_preamble.py
    # пишет его как отдельный run). Если по какой-то причине Word разбил
    # его на несколько ranов, fallback ниже всё равно сшивает текст
    # параграфа и подменяет содержимое первого подходящего run'а.
    for para in doc.paragraphs:
        full_text = "".join(r.text for r in para.runs)
        if "__PG__" not in full_text:
            continue
        m = PLACEHOLDER.search(full_text)
        if not m:
            continue
        title = m.group(1)
        page = find_first_page(pages, title)
        replacement = str(page) if page else ""

        # Простой случай: один run содержит всё.
        ok = False
        for r in para.runs:
            if PLACEHOLDER.search(r.text):
                r.text = PLACEHOLDER.sub(replacement, r.text)
                ok = True
                break
        if not ok:
            # Fallback: переписываем все runs за счёт первого.
            joined = PLACEHOLDER.sub(replacement, full_text)
            for i, r in enumerate(para.runs):
                r.text = joined if i == 0 else ""

        if page:
            replaced += 1
        else:
            missed += 1

    doc.save(str(docx_path))
    print(f"✓ TOC: проставлено {replaced} номеров страниц "
          f"({missed} не найдены) в {docx_path.name}")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(
            "Usage: fill_toc.py <docx_path> <pdf_path>"
        )
    fill(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())


if __name__ == "__main__":
    main()
