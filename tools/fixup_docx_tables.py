"""Постобработка docx: привести все таблицы к ГОСТ-виду.

Pandoc для pipe-таблицы задаёт ширины колонок пропорционально количеству
дефисов между `|` в разделителе. Однако `<w:tblW>` он ставит узким
(≈ 2300 twips = 23 % страницы), а к ячейкам наследует first-line-indent
из стиля Normal (1.25 см). Этот скрипт:

1. Для каждой таблицы (`<w:tbl>`):
   - переписывает `<w:tblW>` на 100 % страницы (`w:type="pct" w:w="5000"`);
   - переводит `<w:tblLayout>` в `autofit`;
   - пропорционально масштабирует `<w:tblGrid w:gridCol>` и
     `<w:tcW>` так, чтобы сумма ширин стала равна полезной ширине
     страницы (9355 twips для A4 с полями 30 мм / 15 мм);
   - назначает стиль `TableGrid` (Word отрисует тонкие чёрные границы);
   - в первой строке проставляет атрибут `<w:tblHeader/>` —
     заголовок повторяется при переносе таблицы на следующую страницу.
2. Внутри каждой ячейки сбрасывает `<w:ind w:firstLine="..."/>` на 0 —
   текст в ячейках без абзацного отступа.

Запуск:
    arch -arm64 .venv/bin/python tools/fixup_docx_tables.py build/Воробьёв_РПЗ.docx
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

# A4 = 11906 twips. Поля 30 мм слева + 15 мм справа = 45 мм
# = 45/25.4*1440 ≈ 2551 twips → полезная ширина 11906 − 2551 ≈ 9355 twips.
PAGE_USABLE_TWIPS = 9355

# Минимальная ширина колонки. 1100 twips ≈ 19 мм — хватает на короткое
# слово вроде «учётку» с padding ячейки.
MIN_COL_TWIPS = 1100


def _extract_column_weights(table: str, ncols: int) -> list[int]:
    """Для каждой колонки оценить «вес» — взвешенную длину содержимого.

    Идея: длина заголовка влияет меньше, чем средняя длина по 5 первым
    строкам. Это даёт реалистичные пропорции для табличных данных.
    """
    rows = re.findall(r"<w:tr\b[^>]*>.*?</w:tr>", table, re.DOTALL)
    col_max = [1] * ncols
    col_sum = [0] * ncols
    col_count = [0] * ncols
    col_max_word = [1] * ncols  # самое длинное слово в колонке (нерасторжимое)
    for r in rows[:20]:  # хватит первых 20 строк для оценки
        cells = re.findall(r"<w:tc\b[^>]*>.*?</w:tc>", r, re.DOTALL)
        for i, c in enumerate(cells[:ncols]):
            text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", c)).strip()
            n = len(text)
            col_max[i] = max(col_max[i], n)
            col_sum[i] += n
            col_count[i] += 1
            for w in re.split(r"[\s\-—–]+", text):
                col_max_word[i] = max(col_max_word[i], len(w))
    weights = []
    for i in range(ncols):
        avg = col_sum[i] / max(col_count[i], 1)
        # Вес — компромисс между максимальной длиной строки и средней.
        # Если самое длинное слово больше — повышаем вес, чтобы оно
        # помещалось в одну строку (не было «Имеет/учётку»).
        base = 0.55 * col_max[i] + 0.45 * avg
        weights.append(max(int(max(base, col_max_word[i] * 1.4)), 4))
    return weights


def _fix_table(table_match: re.Match) -> str:
    table = table_match.group(0)

    # 1) Пропорционально масштабировать gridCol на полезную ширину страницы.
    grid_match = re.search(r"<w:tblGrid>(.*?)</w:tblGrid>", table, re.DOTALL)
    if grid_match:
        grid_body = grid_match.group(1)
        cols = [int(m.group(1)) for m in re.finditer(r'w:w="(\d+)"', grid_body)]
        if cols and sum(cols) > 0:
            # Если все колонки одинаковые (pandoc-pipe), масштабируем
            # ширины по длине текста в заголовке. Иначе уважаем
            # уже заданные пропорции (grid-таблица).
            uniform = len(set(cols)) == 1
            if uniform:
                weights = _extract_column_weights(table, len(cols))
                if weights and len(weights) == len(cols):
                    cols = weights

            # Распределяем ширину так, чтобы:
            #  (а) у каждой колонки было не меньше MIN_COL_TWIPS;
            #  (б) сумма равна PAGE_USABLE_TWIPS;
            #  (в) колонки сохраняли пропорции весов в свободной части.
            ncols = len(cols)
            free = max(PAGE_USABLE_TWIPS - MIN_COL_TWIPS * ncols, 0)
            total_w = sum(cols)
            if total_w == 0 or free == 0:
                new_cols = [PAGE_USABLE_TWIPS // ncols] * ncols
            else:
                new_cols = [
                    MIN_COL_TWIPS + int(c * free / total_w) for c in cols
                ]
            diff = PAGE_USABLE_TWIPS - sum(new_cols)
            if new_cols:
                new_cols[-1] += diff

            new_grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in new_cols)
            table = table.replace(
                grid_match.group(0),
                f"<w:tblGrid>{new_grid}</w:tblGrid>",
            )

            # Заменить w:tcW в каждой ячейке индексной колонки.
            def _row(row_match: re.Match) -> str:
                row = row_match.group(0)
                cell_idx = -1

                def _cell(cell_match: re.Match) -> str:
                    nonlocal cell_idx
                    cell_idx += 1
                    if cell_idx >= len(new_cols):
                        return cell_match.group(0)
                    cell = cell_match.group(0)
                    target_w = new_cols[cell_idx]
                    if "<w:tcW" in cell:
                        cell = re.sub(
                            r"<w:tcW[^/]*/>",
                            f'<w:tcW w:type="dxa" w:w="{target_w}"/>',
                            cell,
                            count=1,
                        )
                    else:
                        if "<w:tcPr />" in cell:
                            cell = cell.replace(
                                "<w:tcPr />",
                                f'<w:tcPr><w:tcW w:type="dxa" w:w="{target_w}"/></w:tcPr>',
                            )
                        elif "<w:tcPr>" in cell:
                            cell = cell.replace(
                                "<w:tcPr>",
                                f'<w:tcPr><w:tcW w:type="dxa" w:w="{target_w}"/>',
                                1,
                            )
                        else:
                            cell = cell.replace(
                                "<w:tc>",
                                f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{target_w}"/></w:tcPr>',
                                1,
                            )
                    return cell

                return re.sub(r"<w:tc>.*?</w:tc>", _cell, row, flags=re.DOTALL)

            table = re.sub(r"<w:tr\b[^>]*>.*?</w:tr>", _row, table, flags=re.DOTALL)

    # 2) <w:tblW> — 100 % ширины страницы.
    if re.search(r"<w:tblW[^/]*/>", table):
        table = re.sub(
            r"<w:tblW[^/]*/>",
            '<w:tblW w:type="pct" w:w="5000"/>',
            table,
        )
    else:
        table = re.sub(
            r"(<w:tblPr>)",
            r'\1<w:tblW w:type="pct" w:w="5000"/>',
            table,
            count=1,
        )

    # 3) <w:tblLayout> — autofit.
    if "<w:tblLayout" in table:
        table = re.sub(
            r"<w:tblLayout[^/]*/>",
            '<w:tblLayout w:type="autofit"/>',
            table,
        )
    else:
        table = re.sub(
            r'(<w:tblW[^/]*/>)',
            r'\1<w:tblLayout w:type="autofit"/>',
            table,
            count=1,
        )

    # 4) Внутри ячеек — убрать first-line-indent.
    def _para_inside(p_match: re.Match) -> str:
        p = p_match.group(0)
        if "<w:pPr>" in p:
            if "<w:ind " in p:
                p = re.sub(
                    r'<w:ind\b[^/]*?firstLine="\d+"[^/]*/>',
                    '<w:ind w:firstLine="0"/>',
                    p,
                )
            else:
                p = p.replace("<w:pPr>", '<w:pPr><w:ind w:firstLine="0"/>', 1)
        else:
            p = re.sub(
                r'<w:p\b([^>]*)>',
                r'<w:p\1><w:pPr><w:ind w:firstLine="0"/></w:pPr>',
                p,
                count=1,
            )
        return p

    def _cell_paras(cell_match: re.Match) -> str:
        cell = cell_match.group(0)
        cell = re.sub(r"<w:p\b[^>]*>.*?</w:p>", _para_inside, cell, flags=re.DOTALL)
        return cell

    table = re.sub(r"<w:tc>.*?</w:tc>", _cell_paras, table, flags=re.DOTALL)

    # 5) Назначить стиль таблицы — Word нарисует границы.
    if '<w:tblStyle ' not in table and "<w:tblPr>" in table:
        table = table.replace(
            "<w:tblPr>",
            '<w:tblPr><w:tblStyle w:val="TableGrid"/>',
            1,
        )

    # 6) Первая строка — повторять заголовок при переносе.
    first_row_match = re.search(r"<w:tr\b[^>]*>.*?</w:tr>", table, re.DOTALL)
    if first_row_match:
        fr = first_row_match.group(0)
        if "<w:tblHeader" not in fr:
            if "<w:trPr>" in fr:
                fr_new = fr.replace("<w:trPr>", "<w:trPr><w:tblHeader/>", 1)
            else:
                fr_new = re.sub(
                    r"(<w:tr\b[^>]*>)",
                    r"\1<w:trPr><w:tblHeader/></w:trPr>",
                    fr, count=1,
                )
            if fr_new != fr:
                table = table.replace(fr, fr_new, 1)
    return table


def fix_document_xml(xml_text: str) -> str:
    return re.sub(r"<w:tbl>.*?</w:tbl>", _fix_table, xml_text, flags=re.DOTALL)


def fixup(docx_path: Path) -> None:
    backup = docx_path.with_suffix(".docx.bak")
    shutil.copy(docx_path, backup)

    tmp = docx_path.with_suffix(".docx.tmp")
    with zipfile.ZipFile(backup, "r") as src, zipfile.ZipFile(tmp, "w",
                                                              zipfile.ZIP_DEFLATED) as dst:
        for item in src.namelist():
            data = src.read(item)
            if item == "word/document.xml":
                data = fix_document_xml(data.decode("utf-8")).encode("utf-8")
            dst.writestr(item, data)

    shutil.move(tmp, docx_path)
    backup.unlink()
    print(f"✓ Таблицы в {docx_path.name}: ширина 100 %, "
          f"колонки пропорционально, заголовок повторяется, ячейки без отступа.")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/Воробьёв_РПЗ.docx")
    fixup(target.resolve())
