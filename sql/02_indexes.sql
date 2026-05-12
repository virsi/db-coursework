-- ============================================================================
-- АС ОУДО — индексы для ускорения поиска и формирования отчётов.
-- Все индексы — простые B-tree, кроме явно отмеченных функциональных.
-- ============================================================================

-- Поиск по логину (используется при каждом входе в систему).
CREATE INDEX IF NOT EXISTS ix_users_login          ON users (login);

-- Поиск/сортировка по ФИО — основная операция в формах.
CREATE INDEX IF NOT EXISTS ix_employees_full_name  ON employees (full_name);
CREATE INDEX IF NOT EXISTS ix_teachers_full_name   ON teachers  (full_name);
CREATE INDEX IF NOT EXISTS ix_students_full_name   ON students  (full_name);

-- Функциональные индексы для регистронезависимого поиска по подстроке
-- через ILIKE в CRUD-формах (см. РПЗ §12.4).
-- LOWER(...) делает применение ILIKE детерминированным и позволяет
-- планировщику использовать индекс при `LOWER(field) LIKE '%...%'`.
CREATE INDEX IF NOT EXISTS ix_employees_fn_lower   ON employees (LOWER(full_name));
CREATE INDEX IF NOT EXISTS ix_teachers_fn_lower    ON teachers  (LOWER(full_name));
CREATE INDEX IF NOT EXISTS ix_students_fn_lower    ON students  (LOWER(full_name));
CREATE INDEX IF NOT EXISTS ix_disciplines_name_lower ON disciplines (LOWER(name));
CREATE INDEX IF NOT EXISTS ix_courses_name_lower   ON courses   (LOWER(name));

-- FK-индексы (PostgreSQL не создаёт их автоматически).
CREATE INDEX IF NOT EXISTS ix_courses_teacher_id    ON courses     (teacher_id);
CREATE INDEX IF NOT EXISTS ix_courses_discipline_id ON courses     (discipline_id);
CREATE INDEX IF NOT EXISTS ix_enrollments_course_id ON enrollments (course_id);
CREATE INDEX IF NOT EXISTS ix_tasks_course_id       ON tasks       (course_id);
CREATE INDEX IF NOT EXISTS ix_variants_task_id      ON variants    (task_id);
CREATE INDEX IF NOT EXISTS ix_contracts_employee_id ON contracts   (employee_id);
CREATE INDEX IF NOT EXISTS ix_contracts_student_id  ON contracts   (student_id);
CREATE INDEX IF NOT EXISTS ix_contracts_teacher_id  ON contracts   (teacher_id);

-- Составной индекс для отчётов «Баллы студента» и «Средний балл».
-- Используется в JOIN grades ↔ tasks ↔ courses.
CREATE INDEX IF NOT EXISTS ix_grades_student_task   ON grades (student_id, task_id);

-- Поиск курса по диапазону дат — для отчёта о текущих курсах.
CREATE INDEX IF NOT EXISTS ix_courses_dates         ON courses (start_date, end_date);
