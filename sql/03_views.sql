-- ============================================================================
-- АС ОУДО — представления (views) для отчётов.
-- Используются в app/services/reports.py и в формах отчётов PyQt.
-- ============================================================================

DROP VIEW IF EXISTS v_student_grades         CASCADE;
DROP VIEW IF EXISTS v_avg_score_per_course   CASCADE;
DROP VIEW IF EXISTS v_avg_score_per_student  CASCADE;
DROP VIEW IF EXISTS v_course_overview        CASCADE;
DROP VIEW IF EXISTS v_enrollment_summary     CASCADE;
DROP VIEW IF EXISTS v_teachers_with_courses  CASCADE;
DROP VIEW IF EXISTS v_score_100_system       CASCADE;

-- Детализированный отчёт «Баллы студента»: все его оценки.
CREATE VIEW v_student_grades AS
SELECT s.id              AS student_id,
       s.full_name       AS student_name,
       c.id              AS course_id,
       c.name            AS course_name,
       d.name            AS discipline_name,
       t.id              AS task_id,
       t.title           AS task_title,
       t.type            AS task_type,
       g.score           AS score,
       t.max_score       AS max_score,
       g.graded_at       AS graded_at
FROM   students    s
JOIN   grades      g ON g.student_id = s.id
JOIN   tasks       t ON t.id = g.task_id
JOIN   courses     c ON c.id = t.course_id
JOIN   disciplines d ON d.id = c.discipline_id;

-- Средний балл по курсу.
CREATE VIEW v_avg_score_per_course AS
SELECT c.id                            AS course_id,
       c.name                          AS course_name,
       d.name                          AS discipline_name,
       te.full_name                    AS teacher_name,
       COUNT(g.id)                     AS grades_count,
       ROUND(AVG(g.score)::numeric, 2) AS avg_score
FROM   courses     c
JOIN   disciplines d  ON d.id  = c.discipline_id
JOIN   teachers    te ON te.id = c.teacher_id
LEFT   JOIN tasks   t ON t.course_id = c.id
LEFT   JOIN grades  g ON g.task_id   = t.id
GROUP BY c.id, c.name, d.name, te.full_name;

-- Средний балл по каждому студенту (для аналитики).
CREATE VIEW v_avg_score_per_student AS
SELECT s.id                            AS student_id,
       s.full_name                     AS student_name,
       COUNT(g.id)                     AS grades_count,
       ROUND(AVG(g.score)::numeric, 2) AS avg_score
FROM   students s
LEFT   JOIN grades g ON g.student_id = s.id
GROUP BY s.id, s.full_name;

-- Список курсов с преподавателем и дисциплиной.
CREATE VIEW v_course_overview AS
SELECT c.id            AS course_id,
       c.name          AS course_name,
       d.name          AS discipline_name,
       d.hours         AS hours,
       te.full_name    AS teacher_name,
       te.position     AS teacher_position,
       c.start_date    AS start_date,
       c.end_date      AS end_date,
       (SELECT COUNT(*) FROM enrollments e
        WHERE e.course_id = c.id AND e.is_active) AS active_students
FROM   courses     c
JOIN   disciplines d  ON d.id  = c.discipline_id
JOIN   teachers    te ON te.id = c.teacher_id;

-- Сводка по записи на курсы.
CREATE VIEW v_enrollment_summary AS
SELECT s.id           AS student_id,
       s.full_name    AS student_name,
       s.status       AS student_status,
       COUNT(e.id) FILTER (WHERE e.is_active)        AS active_enrollments,
       COUNT(e.id) FILTER (WHERE NOT e.is_active)    AS inactive_enrollments,
       MIN(e.enrollment_date)                        AS first_enrollment,
       MAX(e.enrollment_date)                        AS last_enrollment
FROM   students s
LEFT   JOIN enrollments e ON e.student_id = s.id
GROUP BY s.id, s.full_name, s.status;

-- Преподаватели и закреплённые за ними курсы.
CREATE VIEW v_teachers_with_courses AS
SELECT te.id              AS teacher_id,
       te.full_name        AS teacher_name,
       te.specialization   AS specialization,
       te.position         AS position,
       COUNT(c.id)         AS courses_count,
       COALESCE(STRING_AGG(c.name, '; ' ORDER BY c.start_date), '') AS courses
FROM   teachers te
LEFT   JOIN courses c ON c.teacher_id = te.id
GROUP BY te.id, te.full_name, te.specialization, te.position;

-- 100-балльная система: пересчёт средней оценки студента в 100-балльную шкалу
-- с учётом веса по типу задания. Формула:
--   score_100 = SUM(score * weight) / SUM(weight)
-- где weight = 0.5 (homework, lab), 1.0 (test, control), 1.5 (essay, coursework),
-- 2.0 (exam).
CREATE VIEW v_score_100_system AS
SELECT s.id                                  AS student_id,
       s.full_name                           AS student_name,
       c.id                                  AS course_id,
       c.name                                AS course_name,
       SUM(g.score * w.weight)               AS weighted_score,
       SUM(w.weight)                         AS total_weight,
       ROUND( (SUM(g.score * w.weight) / NULLIF(SUM(w.weight), 0))::numeric, 2)
                                             AS score_100
FROM   students s
JOIN   grades   g ON g.student_id = s.id
JOIN   tasks    t ON t.id = g.task_id
JOIN   courses  c ON c.id = t.course_id
JOIN   LATERAL (
           SELECT CASE t.type
                      WHEN 'homework'   THEN 0.5
                      WHEN 'lab'        THEN 0.5
                      WHEN 'test'       THEN 1.0
                      WHEN 'control'    THEN 1.0
                      WHEN 'essay'      THEN 1.5
                      WHEN 'coursework' THEN 1.5
                      WHEN 'exam'       THEN 2.0
                  END AS weight
       ) w ON TRUE
GROUP BY s.id, s.full_name, c.id, c.name;
