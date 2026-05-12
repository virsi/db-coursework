-- ============================================================================
-- АС ОУДО — тестовые данные.
-- Пароли всех учётных записей равны их логину для удобства демонстрации.
-- Хеши генерируются через pgcrypto (bcrypt cost=10), совместимы с
-- проверкой через Python-библиотеку bcrypt в приложении.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

TRUNCATE grades, variants, tasks, contracts, enrollments,
         courses, disciplines, students, teachers, employees, users
         RESTART IDENTITY CASCADE;

-- ----------------------------------------------------------------------------
-- USERS + EMPLOYEES (3 администратора)
-- ----------------------------------------------------------------------------
WITH new_users AS (
    INSERT INTO users (login, password_hash, role) VALUES
        ('admin',    crypt('admin',    gen_salt('bf', 10)), 'admin'),
        ('manager1', crypt('manager1', gen_salt('bf', 10)), 'admin'),
        ('manager2', crypt('manager2', gen_salt('bf', 10)), 'admin')
    RETURNING id, login
)
INSERT INTO employees (user_id, full_name, position, access_level)
SELECT id,
       CASE login
           WHEN 'admin'    THEN 'Иванов Иван Иванович'
           WHEN 'manager1' THEN 'Петров Пётр Петрович'
           WHEN 'manager2' THEN 'Сидорова Анна Сергеевна'
       END,
       CASE login
           WHEN 'admin'    THEN 'Главный администратор'
           WHEN 'manager1' THEN 'Менеджер по работе со студентами'
           WHEN 'manager2' THEN 'Менеджер учебной части'
       END,
       (CASE login WHEN 'admin' THEN 'super' ELSE 'extended' END)::access_level
FROM new_users;

-- ----------------------------------------------------------------------------
-- USERS + TEACHERS (5 преподавателей)
-- ----------------------------------------------------------------------------
WITH new_users AS (
    INSERT INTO users (login, password_hash, role) VALUES
        ('teacher1', crypt('teacher1', gen_salt('bf', 10)), 'teacher'),
        ('teacher2', crypt('teacher2', gen_salt('bf', 10)), 'teacher'),
        ('teacher3', crypt('teacher3', gen_salt('bf', 10)), 'teacher'),
        ('teacher4', crypt('teacher4', gen_salt('bf', 10)), 'teacher'),
        ('teacher5', crypt('teacher5', gen_salt('bf', 10)), 'teacher')
    RETURNING id, login
)
INSERT INTO teachers (user_id, full_name, position, specialization)
SELECT id,
       CASE login
           WHEN 'teacher1' THEN 'Ахметова Фаина Борисовна'
           WHEN 'teacher2' THEN 'Кузнецов Дмитрий Алексеевич'
           WHEN 'teacher3' THEN 'Соколова Елена Викторовна'
           WHEN 'teacher4' THEN 'Морозов Александр Николаевич'
           WHEN 'teacher5' THEN 'Васильева Ольга Михайловна'
       END,
       CASE login
           WHEN 'teacher1' THEN 'Доцент'
           WHEN 'teacher2' THEN 'Старший преподаватель'
           WHEN 'teacher3' THEN 'Профессор'
           WHEN 'teacher4' THEN 'Доцент'
           WHEN 'teacher5' THEN 'Старший преподаватель'
       END,
       CASE login
           WHEN 'teacher1' THEN 'Высшая математика'
           WHEN 'teacher2' THEN 'Программирование на Python'
           WHEN 'teacher3' THEN 'Базы данных'
           WHEN 'teacher4' THEN 'Физика'
           WHEN 'teacher5' THEN 'Иностранные языки'
       END
FROM new_users;

-- ----------------------------------------------------------------------------
-- USERS + STUDENTS (30 студентов)
-- ----------------------------------------------------------------------------
WITH numbers AS (
    SELECT generate_series(1, 30) AS n
),
fios AS (
    SELECT n,
           CASE n
               WHEN 1  THEN 'Воробьёв Егор Александрович'
               WHEN 2  THEN 'Смирнова Анастасия Дмитриевна'
               WHEN 3  THEN 'Попов Артём Сергеевич'
               WHEN 4  THEN 'Лебедева Мария Андреевна'
               WHEN 5  THEN 'Козлов Никита Игоревич'
               WHEN 6  THEN 'Новикова Дарья Павловна'
               WHEN 7  THEN 'Морозов Илья Алексеевич'
               WHEN 8  THEN 'Волкова Ксения Михайловна'
               WHEN 9  THEN 'Соловьёв Максим Андреевич'
               WHEN 10 THEN 'Зайцева Полина Викторовна'
               WHEN 11 THEN 'Павлов Денис Александрович'
               WHEN 12 THEN 'Семёнова Виктория Ивановна'
               WHEN 13 THEN 'Голубев Артур Олегович'
               WHEN 14 THEN 'Виноградова Александра Романовна'
               WHEN 15 THEN 'Богданов Кирилл Юрьевич'
               WHEN 16 THEN 'Воробьёва Софья Александровна'
               WHEN 17 THEN 'Фёдоров Григорий Михайлович'
               WHEN 18 THEN 'Михайлова Алина Дмитриевна'
               WHEN 19 THEN 'Беляев Тимофей Сергеевич'
               WHEN 20 THEN 'Тарасова Юлия Андреевна'
               WHEN 21 THEN 'Белов Данила Романович'
               WHEN 22 THEN 'Комарова Ева Викторовна'
               WHEN 23 THEN 'Орлов Семён Антонович'
               WHEN 24 THEN 'Киселёва Алиса Павловна'
               WHEN 25 THEN 'Макаров Лев Игоревич'
               WHEN 26 THEN 'Андреева Варвара Кирилловна'
               WHEN 27 THEN 'Ковалёв Платон Денисович'
               WHEN 28 THEN 'Ильина Маргарита Олеговна'
               WHEN 29 THEN 'Гусев Матвей Александрович'
               WHEN 30 THEN 'Степанова Вероника Сергеевна'
           END AS full_name
    FROM numbers
),
new_users AS (
    INSERT INTO users (login, password_hash, role)
    SELECT 'student' || n,
           crypt('student' || n, gen_salt('bf', 10)),
           'student'
    FROM numbers
    RETURNING id, login
)
INSERT INTO students (user_id, full_name, enrollment_date, status)
SELECT u.id,
       f.full_name,
       DATE '2023-09-01' + (random() * 600)::int,
       (CASE
           WHEN n <= 25 THEN 'studying'
           WHEN n  = 26 THEN 'academic_leave'
           WHEN n  = 27 THEN 'graduated'
           WHEN n  = 28 THEN 'graduated'
           ELSE              'expelled'
       END)::student_status
FROM new_users u
JOIN fios f ON f.n::text = REPLACE(u.login, 'student', '');

-- ----------------------------------------------------------------------------
-- DISCIPLINES (10 дисциплин)
-- ----------------------------------------------------------------------------
INSERT INTO disciplines (name, hours, description) VALUES
    ('Высшая математика',          144, 'Линейная алгебра, матанализ, дискретная математика'),
    ('Программирование на Python', 108, 'Основы языка, ООП, стандартная библиотека'),
    ('Базы данных',                 96, 'Реляционная модель, SQL, нормализация, СУБД'),
    ('Физика',                     128, 'Механика, электродинамика, термодинамика'),
    ('Иностранный язык',           160, 'Английский язык: общий и технический'),
    ('Алгоритмы и структуры данных', 96, 'Сортировки, графы, динамическое программирование'),
    ('Операционные системы',        80, 'Процессы, потоки, память, файловые системы'),
    ('Компьютерные сети',           80, 'Стек TCP/IP, маршрутизация, безопасность'),
    ('Веб-разработка',              72, 'HTTP, REST, фронтенд и бэкенд'),
    ('Машинное обучение',          112, 'Линейная регрессия, деревья, нейросети');

-- ----------------------------------------------------------------------------
-- COURSES (15 курсов на основе 10 дисциплин)
-- ----------------------------------------------------------------------------
INSERT INTO courses (name, start_date, end_date, teacher_id, discipline_id) VALUES
    ('Математика для самых маленьких 2024-2025', '2024-09-01', '2025-05-31', 1,  1),
    ('Высшая математика — продвинутый поток',     '2024-09-01', '2025-05-31', 1,  1),
    ('Python с нуля',                              '2024-10-01', '2025-04-30', 2,  2),
    ('Промышленная разработка на Python',          '2025-02-01', '2025-06-30', 2,  2),
    ('Базы данных: основы',                        '2024-09-15', '2025-01-31', 3,  3),
    ('PostgreSQL для разработчиков',               '2025-02-15', '2025-06-15', 3,  3),
    ('Общая физика',                               '2024-09-01', '2025-05-15', 4,  4),
    ('English for IT',                             '2024-09-10', '2025-05-30', 5,  5),
    ('Алгоритмы и структуры данных',               '2024-10-01', '2025-04-30', 2,  6),
    ('Внутреннее устройство ОС',                   '2025-02-01', '2025-06-30', 4,  7),
    ('Компьютерные сети: введение',                '2024-09-01', '2025-01-31', 4,  8),
    ('Современная веб-разработка',                 '2025-02-01', '2025-06-30', 2,  9),
    ('Введение в машинное обучение',               '2024-10-15', '2025-05-31', 3, 10),
    ('Углублённый английский',                     '2025-02-01', '2025-06-30', 5,  5),
    ('Дискретная математика',                      '2024-09-01', '2025-01-15', 1,  1);

-- ----------------------------------------------------------------------------
-- ENROLLMENTS — каждый «учится» подписан на 4 случайных курса.
-- ----------------------------------------------------------------------------
INSERT INTO enrollments (student_id, course_id, enrollment_date, is_active)
SELECT s.id, c.id,
       DATE '2024-09-01' + (random() * 60)::int,
       TRUE
FROM   students s
CROSS  JOIN LATERAL (
           SELECT id FROM courses ORDER BY random() LIMIT 4
       ) c
WHERE  s.status IN ('studying', 'academic_leave')
ON CONFLICT (student_id, course_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- CONTRACTS — договор об обучении со всеми студентами «учится»
--              и трудовой со всеми преподавателями.
-- ----------------------------------------------------------------------------
INSERT INTO contracts (employee_id, student_id, teacher_id,
                       contract_type, contract_date, is_active)
SELECT 1, s.id, NULL, 'education', s.enrollment_date, TRUE
FROM   students s
WHERE  s.status IN ('studying', 'academic_leave', 'graduated');

INSERT INTO contracts (employee_id, student_id, teacher_id,
                       contract_type, contract_date, is_active)
SELECT 1, NULL, t.id, 'employment', DATE '2024-08-15', TRUE
FROM   teachers t;

-- ----------------------------------------------------------------------------
-- TASKS — на каждый курс по 4 задания разных типов.
-- ----------------------------------------------------------------------------
INSERT INTO tasks (course_id, title, description, type, deadline, max_score)
SELECT c.id,
       'Задание ' || k.n || ' по курсу «' || c.name || '»',
       'Описание задания ' || k.n,
       (ARRAY['homework','lab','test','control','essay','coursework','exam']::task_type[])
           [1 + (k.n - 1) % 7],
       c.start_date + make_interval(days => k.n * 30),
       100
FROM   courses c
CROSS  JOIN generate_series(1, 4) AS k(n);

-- ----------------------------------------------------------------------------
-- VARIANTS — у каждой контрольной/лабораторной 3 варианта.
-- ----------------------------------------------------------------------------
INSERT INTO variants (task_id, number, description)
SELECT t.id, v, 'Вариант ' || v || ' к заданию «' || t.title || '»'
FROM   tasks t
CROSS  JOIN generate_series(1, 3) AS v
WHERE  t.type IN ('lab', 'control', 'test', 'exam');

-- ----------------------------------------------------------------------------
-- GRADES — каждому записанному студенту ставим оценки по заданиям его курсов
--          (с вероятностью 80%). Случайные оценки 50–100.
-- ----------------------------------------------------------------------------
INSERT INTO grades (student_id, task_id, score, graded_at)
SELECT e.student_id,
       t.id,
       50 + (random() * 50)::int,
       t.deadline + make_interval(days => (random() * 7)::int)
FROM   enrollments e
JOIN   tasks       t ON t.course_id = e.course_id
WHERE  e.is_active
  AND  random() < 0.8
ON CONFLICT (student_id, task_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Проверочный вывод: сколько строк получилось.
-- ----------------------------------------------------------------------------
SELECT 'users'        AS table_name, COUNT(*) FROM users        UNION ALL
SELECT 'employees',                  COUNT(*) FROM employees    UNION ALL
SELECT 'teachers',                   COUNT(*) FROM teachers     UNION ALL
SELECT 'students',                   COUNT(*) FROM students     UNION ALL
SELECT 'disciplines',                COUNT(*) FROM disciplines  UNION ALL
SELECT 'courses',                    COUNT(*) FROM courses      UNION ALL
SELECT 'enrollments',                COUNT(*) FROM enrollments  UNION ALL
SELECT 'contracts',                  COUNT(*) FROM contracts    UNION ALL
SELECT 'tasks',                      COUNT(*) FROM tasks        UNION ALL
SELECT 'variants',                   COUNT(*) FROM variants     UNION ALL
SELECT 'grades',                     COUNT(*) FROM grades;
