"""Сервис отчётов: запросы к представлениям БД для §15/§17 РПЗ."""

from app.db.connection import Database


def course_overview() -> list[dict]:
    """Список курсов с дисциплиной, преподавателем и числом активных студентов."""
    with Database.cursor() as cur:
        cur.execute("SELECT * FROM v_course_overview ORDER BY start_date DESC")
        return [dict(r) for r in cur.fetchall()]


def enrollment_summary() -> list[dict]:
    """Сводка по записи студентов на курсы."""
    with Database.cursor() as cur:
        cur.execute("SELECT * FROM v_enrollment_summary ORDER BY student_name")
        return [dict(r) for r in cur.fetchall()]


def teachers_with_courses() -> list[dict]:
    """Преподаватели и их курсы."""
    with Database.cursor() as cur:
        cur.execute("SELECT * FROM v_teachers_with_courses ORDER BY teacher_name")
        return [dict(r) for r in cur.fetchall()]


def average_score_per_course() -> list[dict]:
    """Средний балл по каждому курсу."""
    with Database.cursor() as cur:
        cur.execute("SELECT * FROM v_avg_score_per_course ORDER BY course_name")
        return [dict(r) for r in cur.fetchall()]


def average_score_per_student() -> list[dict]:
    """Средний балл по каждому студенту."""
    with Database.cursor() as cur:
        cur.execute("SELECT * FROM v_avg_score_per_student ORDER BY avg_score DESC NULLS LAST")
        return [dict(r) for r in cur.fetchall()]


def student_grades(student_id: int | None = None) -> list[dict]:
    """Детальный отчёт «Баллы студента»."""
    sql = "SELECT * FROM v_student_grades"
    params: list = []
    if student_id is not None:
        sql += " WHERE student_id = %s"
        params.append(student_id)
    sql += " ORDER BY student_name, course_name, graded_at"
    with Database.cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def score_100_system(student_id: int | None = None) -> list[dict]:
    """Отчёт «100-балльная система»: взвешенный итог по курсам."""
    sql = "SELECT * FROM v_score_100_system"
    params: list = []
    if student_id is not None:
        sql += " WHERE student_id = %s"
        params.append(student_id)
    sql += " ORDER BY student_name, course_name"
    with Database.cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
