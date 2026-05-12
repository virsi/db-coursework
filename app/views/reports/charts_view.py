"""Графические отчёты на базе Qt Charts (см. РПЗ §15.6).

Окно содержит две вкладки:

* «Средний балл по курсу» — столбчатая диаграмма; источник — представление
  `v_avg_score_per_course` (см. `sql/03_views.sql`).
* «Распределение студентов по статусам» — круговая диаграмма; считается
  агрегатным запросом по таблице `students` с группировкой по `status`.

Аналог отчёта «Студенты по курсам» из работы dehwyy (см. сравнение в РПЗ),
адаптированный к домену АС ОУДО (3 роли, 4 статуса студента).
"""

from PyQt5.QtChart import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.db.connection import Database
from app.services.reports import average_score_per_course


STATUS_LABELS = {
    "studying":       "Учится",
    "academic_leave": "Академический отпуск",
    "expelled":       "Отчислен",
    "graduated":      "Окончил",
}


def _students_by_status() -> list[tuple[str, int]]:
    with Database.cursor() as cur:
        cur.execute(
            "SELECT status::text AS status, COUNT(*) AS cnt "
            "FROM students GROUP BY status ORDER BY cnt DESC"
        )
        return [(STATUS_LABELS.get(r["status"], r["status"]), r["cnt"])
                for r in cur.fetchall()]


class ChartsReportView(QWidget):
    """Диалоговое окно с двумя графическими отчётами."""

    title = "Аналитика (графические отчёты)"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"АС ОУДО — {self.title}")
        self.resize(960, 640)
        self._build()
        self.refresh()

    # --------------------------------------------------------------- UI ----
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel(self.title)
        font = header.font()
        font.setPointSize(14)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.bar_view = QChartView()
        self.bar_view.setRenderHint(QPainter.Antialiasing)
        self.tabs.addTab(self.bar_view, "Средний балл по курсу")

        self.pie_view = QChartView()
        self.pie_view.setRenderHint(QPainter.Antialiasing)
        self.tabs.addTab(self.pie_view, "Студенты по статусам")

        bottom = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)
        close_btn = QPushButton("Закрыть")
        close_btn.setProperty("role", "secondary")
        close_btn.clicked.connect(self.close)
        bottom.addWidget(refresh_btn)
        bottom.addStretch(1)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    # ----------------------------------------------------------- данные ----
    def refresh(self) -> None:
        self._render_bar_chart()
        self._render_pie_chart()

    def _render_bar_chart(self) -> None:
        data = average_score_per_course()
        # Берём топ-12 курсов по среднему баллу — иначе подписи нечитаемы.
        rows = sorted(
            (r for r in data if r.get("avg_score") is not None),
            key=lambda r: float(r["avg_score"]),
            reverse=True,
        )[:12]

        bar_set = QBarSet("Средний балл")
        categories: list[str] = []
        max_value = 0.0
        for r in rows:
            value = float(r["avg_score"])
            bar_set.append(value)
            short = (r["course_name"] or "")[:28]
            categories.append(short)
            max_value = max(max_value, value)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Средний балл по курсу (топ-12)")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_x.setLabelsAngle(-45)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(100.0, max_value + 5))
        axis_y.setLabelFormat("%.0f")
        axis_y.setTitleText("Баллы")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)
        self.bar_view.setChart(chart)

    def _render_pie_chart(self) -> None:
        rows = _students_by_status()
        series = QPieSeries()
        total = sum(cnt for _, cnt in rows) or 1
        for label, cnt in rows:
            slice_ = series.append(f"{label} — {cnt}", cnt)
            slice_.setLabelVisible(True)
            slice_.setLabel(f"{label}: {cnt} ({cnt * 100 / total:.1f}%)")

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Распределение студентов по статусам (всего {total})")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignRight)
        self.pie_view.setChart(chart)
