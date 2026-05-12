"""Печать таблиц и одиночных карточек через QTextDocument + QPrintPreviewDialog."""

from datetime import datetime
from typing import Sequence

from PyQt5.QtGui import QPageLayout, QTextDocument
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt5.QtWidgets import QWidget


def _html_table(title: str, headers: Sequence[str],
                fields: Sequence[str], rows: list[dict]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{'' if row.get(f) is None else str(row.get(f))}</td>"
            for f in fields
        )
        body_rows.append(f"<tr>{cells}</tr>")
    body = "".join(body_rows)
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f"""
        <html>
        <head><meta charset='utf-8'></head>
        <body style='font-family: Arial, sans-serif;'>
            <h2 style='text-align:center'>{title}</h2>
            <p style='text-align:right; color:#666; font-size:10pt'>
                Сформировано: {timestamp}
            </p>
            <table border='1' cellspacing='0' cellpadding='4'
                   style='border-collapse:collapse; width:100%; font-size:10pt'>
                <thead style='background:#eee'><tr>{head}</tr></thead>
                <tbody>{body}</tbody>
            </table>
        </body>
        </html>
    """


def print_table(parent: QWidget, title: str, headers: Sequence[str],
                fields: Sequence[str], rows: list[dict]) -> None:
    """Открыть диалог предпросмотра печати для табличных данных."""
    document = QTextDocument()
    document.setHtml(_html_table(title, headers, fields, rows))
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageOrientation(QPageLayout.Landscape)
    dialog = QPrintPreviewDialog(printer, parent)
    dialog.setWindowTitle(f"Предпросмотр печати — {title}")
    dialog.paintRequested.connect(document.print_)
    dialog.exec_()


def _html_card(title: str, header: str,
               rows: list[tuple[str, str]],
               detail_title: str | None = None,
               detail_headers: Sequence[str] | None = None,
               detail_rows: list[Sequence[str]] | None = None) -> str:
    """Сформировать HTML «карточки» одной сущности: реквизиты + таблица деталей."""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    fields_html = "".join(
        f"<tr><td style='padding:4px 12px; color:#666; width:200px'>{label}:</td>"
        f"<td style='padding:4px 12px'><b>{value}</b></td></tr>"
        for label, value in rows
    )
    detail_html = ""
    if detail_headers and detail_rows is not None:
        head = "".join(f"<th>{h}</th>" for h in detail_headers)
        body_rows = []
        for row in detail_rows:
            cells = "".join(f"<td>{c}</td>" for c in row)
            body_rows.append(f"<tr>{cells}</tr>")
        body = "".join(body_rows) if body_rows else (
            f"<tr><td colspan='{len(detail_headers)}' style='text-align:center; color:#888'>"
            f"— нет данных —</td></tr>"
        )
        detail_html = f"""
            <h3 style='margin-top:24px'>{detail_title or ''}</h3>
            <table border='1' cellspacing='0' cellpadding='4'
                   style='border-collapse:collapse; width:100%; font-size:10pt'>
                <thead style='background:#eee'><tr>{head}</tr></thead>
                <tbody>{body}</tbody>
            </table>
        """

    return f"""
        <html>
        <head><meta charset='utf-8'></head>
        <body style='font-family: Arial, sans-serif;'>
            <div style='text-align:center; font-size:9pt; color:#888'>
                АС ОУДО — Автоматизированная система образовательного учреждения
                дистанционного обучения
            </div>
            <h2 style='text-align:center; margin:8px 0'>{title}</h2>
            <h3 style='text-align:center; margin:0 0 12px 0; color:#222'>{header}</h3>
            <p style='text-align:right; color:#666; font-size:10pt'>
                Сформировано: {timestamp}
            </p>
            <table style='border-collapse:collapse; margin:0 auto;'>
                {fields_html}
            </table>
            {detail_html}
        </body>
        </html>
    """


def print_card(parent: QWidget, title: str, header: str,
               rows: list[tuple[str, str]],
               detail_title: str | None = None,
               detail_headers: Sequence[str] | None = None,
               detail_rows: list[Sequence[str]] | None = None) -> None:
    """Открыть диалог предпросмотра печати «карточки» одной сущности.

    rows — список пар (надпись, значение); detail_* — опциональная подчинённая
    таблица (например, оценки студента).
    """
    document = QTextDocument()
    document.setHtml(
        _html_card(title, header, rows,
                   detail_title=detail_title,
                   detail_headers=detail_headers,
                   detail_rows=detail_rows)
    )
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageOrientation(QPageLayout.Portrait)
    dialog = QPrintPreviewDialog(printer, parent)
    dialog.setWindowTitle(f"Предпросмотр печати — {title}")
    dialog.paintRequested.connect(document.print_)
    dialog.exec_()
