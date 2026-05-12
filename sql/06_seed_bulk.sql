-- ============================================================================
-- АС ОУДО — синтетические «продакшен-объёмы» данных для §17 РПЗ.
-- Дополняет 04_seed.sql: добавляет 2 000 студентов, 200 курсов, ≈ 100 000
-- оценок. После прогона можно делать осмысленный EXPLAIN ANALYZE.
--
-- Совместимо с 04_seed.sql: на момент запуска уже есть 10 дисциплин и
-- 5 преподавателей. Все вставки идут с ON CONFLICT DO NOTHING, чтобы
-- скрипт был идемпотентным.
-- ============================================================================

\timing on

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------------------------------------------------------
-- BULK USERS + STUDENTS — 2 000 студентов (login = bulk_student_NNNN).
-- pgcrypto.crypt() с cost=4 (а не 10), потому что на 2 000 хешей даже на
-- M1 это +20 секунд против ≈ 1 секунды; для синтетического seed это
-- приемлемо. Реальные пароли seed-аккаунтов остаются в 04_seed.sql c cost=10.
-- ----------------------------------------------------------------------------
WITH new_users AS (
    INSERT INTO users (login, password_hash, role)
    SELECT 'bulk_student_' || LPAD(n::text, 4, '0'),
           crypt('bulk_pwd_' || n, gen_salt('bf', 4)),
           'student'::user_role
    FROM   generate_series(1, 2000) AS n
    ON CONFLICT (login) DO NOTHING
    RETURNING id, login
)
INSERT INTO students (user_id, full_name, enrollment_date, status)
SELECT u.id,
       'Bulk-студент №' || REPLACE(u.login, 'bulk_student_', ''),
       DATE '2023-09-01' + ((random() * 700)::int),
       (ARRAY['studying','studying','studying','studying',
              'academic_leave','graduated','expelled']::student_status[])
           [1 + (random() * 6)::int]
FROM   new_users u;

-- ----------------------------------------------------------------------------
-- BULK COURSES — 200 курсов на базе 10 существующих дисциплин и 5 преподавателей.
-- ----------------------------------------------------------------------------
WITH params AS (
    SELECT n,
           DATE '2024-09-01' + ((random() * 60)::int)  AS sd
    FROM   generate_series(1, 200) AS n
)
INSERT INTO courses (name, start_date, end_date, teacher_id, discipline_id)
SELECT 'Bulk-курс №' || LPAD(p.n::text, 3, '0'),
       p.sd,
       p.sd + (90 + (random() * 180)::int),
       1 + (random() * 4)::int,
       1 + (random() * 9)::int
FROM   params p;

-- ----------------------------------------------------------------------------
-- BULK ENROLLMENTS — каждый bulk-студент записан на 5 случайных bulk-курсов.
-- ----------------------------------------------------------------------------
INSERT INTO enrollments (student_id, course_id, enrollment_date, is_active)
SELECT s.id, c.id,
       DATE '2024-09-01' + ((random() * 60)::int),
       TRUE
FROM   students s
CROSS  JOIN LATERAL (
           SELECT id FROM courses
           WHERE  name LIKE 'Bulk-курс%'
           ORDER  BY random()
           LIMIT  5
       ) c
WHERE  s.full_name LIKE 'Bulk-студент%'
ON CONFLICT (student_id, course_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- BULK TASKS — у каждого bulk-курса по 10 заданий разных типов.
-- ----------------------------------------------------------------------------
INSERT INTO tasks (course_id, title, description, type, deadline, max_score)
SELECT c.id,
       'Bulk-задание ' || k.n || ' к курсу ' || c.id,
       'Сгенерированное задание для нагрузочного тестирования.',
       (ARRAY['homework','lab','test','control','essay','coursework','exam']::task_type[])
           [1 + ((k.n - 1) % 7)],
       c.start_date + make_interval(days => k.n * 14),
       100
FROM   courses c
CROSS  JOIN generate_series(1, 10) AS k(n)
WHERE  c.name LIKE 'Bulk-курс%';

-- ----------------------------------------------------------------------------
-- BULK GRADES — оценки по каждой записи и каждому заданию её курса
--               (с вероятностью 70%). Это ≈ 70 000 оценок.
-- ----------------------------------------------------------------------------
INSERT INTO grades (student_id, task_id, score, graded_at)
SELECT e.student_id,
       t.id,
       40 + (random() * 60)::int,
       t.deadline + make_interval(days => (random() * 7)::int)
FROM   enrollments e
JOIN   tasks       t ON t.course_id = e.course_id
JOIN   courses     c ON c.id        = e.course_id
WHERE  c.name LIKE 'Bulk-курс%'
  AND  e.is_active
  AND  random() < 0.7
ON CONFLICT (student_id, task_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- ANALYZE для актуализации статистики планировщика — критично для §17.
-- ----------------------------------------------------------------------------
ANALYZE users;
ANALYZE students;
ANALYZE courses;
ANALYZE enrollments;
ANALYZE tasks;
ANALYZE grades;

-- ----------------------------------------------------------------------------
-- Контрольные размеры таблиц после загрузки.
-- ----------------------------------------------------------------------------
SELECT relname       AS table_name,
       n_live_tup    AS approx_rows
FROM   pg_stat_user_tables
WHERE  relname IN ('users','students','courses','enrollments','tasks','grades')
ORDER  BY relname;
