-- ============================================================================
-- АС ОУДО — Автоматизированная Система Образовательного Учреждения
-- Дистанционного Обучения. Схема базы данных PostgreSQL.
-- Создание: docs/РПЗ.md §12 «Датологическая модель».
-- Совместимо с PostgreSQL 13+; в проекте используется 17.
-- ============================================================================

DROP TABLE IF EXISTS grades, variants, tasks, contracts, enrollments,
                     courses, disciplines, students, teachers, employees,
                     users CASCADE;

DROP TYPE  IF EXISTS user_role        CASCADE;
DROP TYPE  IF EXISTS access_level     CASCADE;
DROP TYPE  IF EXISTS student_status   CASCADE;
DROP TYPE  IF EXISTS task_type        CASCADE;
DROP TYPE  IF EXISTS contract_type    CASCADE;

-- ----------------------------------------------------------------------------
-- Пользовательские перечислимые типы (см. РПЗ §12.3).
-- Идиоматичны для PostgreSQL: используют минимум памяти, проверяются на
-- этапе INSERT/UPDATE без необходимости в CHECK-выражении.
-- ----------------------------------------------------------------------------
CREATE TYPE user_role      AS ENUM ('admin', 'teacher', 'student');
CREATE TYPE access_level   AS ENUM ('standard', 'extended', 'super');
CREATE TYPE student_status AS ENUM ('studying', 'academic_leave',
                                    'expelled', 'graduated');
CREATE TYPE task_type      AS ENUM ('homework', 'lab', 'test', 'control',
                                    'essay', 'coursework', 'exam');
CREATE TYPE contract_type  AS ENUM ('education', 'employment');

-- ----------------------------------------------------------------------------
-- 1. Аутентификация: единая таблица учётных записей.
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    login           VARCHAR(64)  NOT NULL UNIQUE,
    password_hash   VARCHAR(72)  NOT NULL,
    role            user_role    NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Сотрудники (администрация).
-- ----------------------------------------------------------------------------
CREATE TABLE employees (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER       NOT NULL UNIQUE
                    REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255)  NOT NULL,
    position        VARCHAR(100)  NOT NULL,
    access_level    access_level  NOT NULL DEFAULT 'standard'
);

-- ----------------------------------------------------------------------------
-- 3. Преподаватели.
-- ----------------------------------------------------------------------------
CREATE TABLE teachers (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER      NOT NULL UNIQUE
                    REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255) NOT NULL,
    position        VARCHAR(100) NOT NULL,
    specialization  VARCHAR(150) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. Студенты.
-- ----------------------------------------------------------------------------
CREATE TABLE students (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER         NOT NULL UNIQUE
                    REFERENCES users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255)    NOT NULL,
    enrollment_date DATE            NOT NULL DEFAULT CURRENT_DATE,
    status          student_status  NOT NULL DEFAULT 'studying'
);

-- ----------------------------------------------------------------------------
-- 5. Дисциплины (учебные предметы).
-- ----------------------------------------------------------------------------
CREATE TABLE disciplines (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    hours           INTEGER      NOT NULL CHECK (hours > 0 AND hours <= 1000),
    description     TEXT
);

-- ----------------------------------------------------------------------------
-- 6. Курсы (поток — конкретная реализация дисциплины в учебном году).
-- ----------------------------------------------------------------------------
CREATE TABLE courses (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    start_date      DATE         NOT NULL,
    end_date        DATE         NOT NULL,
    teacher_id      INTEGER      NOT NULL
                    REFERENCES teachers(id) ON DELETE RESTRICT,
    discipline_id   INTEGER      NOT NULL
                    REFERENCES disciplines(id) ON DELETE RESTRICT,
    CHECK (end_date > start_date)
);

-- ----------------------------------------------------------------------------
-- 7. Запись студента на курс (M:N студенты ↔ курсы).
-- ----------------------------------------------------------------------------
CREATE TABLE enrollments (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER      NOT NULL
                    REFERENCES students(id) ON DELETE CASCADE,
    course_id       INTEGER      NOT NULL
                    REFERENCES courses(id) ON DELETE CASCADE,
    enrollment_date DATE         NOT NULL DEFAULT CURRENT_DATE,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    UNIQUE (student_id, course_id)
);

-- ----------------------------------------------------------------------------
-- 8. Договоры. Полиморфная связь: договор заключается сотрудником
--    либо со студентом (тип «об обучении»), либо с преподавателем
--    (тип «трудовой»). Контролируется CHECK-ограничением.
-- ----------------------------------------------------------------------------
CREATE TABLE contracts (
    id              SERIAL PRIMARY KEY,
    employee_id     INTEGER        NOT NULL
                    REFERENCES employees(id) ON DELETE RESTRICT,
    student_id      INTEGER
                    REFERENCES students(id) ON DELETE CASCADE,
    teacher_id      INTEGER
                    REFERENCES teachers(id) ON DELETE CASCADE,
    contract_type   contract_type  NOT NULL,
    contract_date   DATE           NOT NULL DEFAULT CURRENT_DATE,
    is_active       BOOLEAN        NOT NULL DEFAULT TRUE,
    -- Ровно одна из сторон договора (студент или преподаватель) заполнена,
    -- и она соответствует типу договора.
    CHECK (
        (contract_type = 'education'  AND student_id IS NOT NULL AND teacher_id IS NULL)
     OR (contract_type = 'employment' AND teacher_id IS NOT NULL AND student_id IS NULL)
    )
);

-- ----------------------------------------------------------------------------
-- 9. Задания, выдаваемые преподавателем в рамках курса.
-- ----------------------------------------------------------------------------
CREATE TABLE tasks (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER      NOT NULL
                    REFERENCES courses(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    type            task_type    NOT NULL,
    deadline        TIMESTAMP    NOT NULL,
    max_score       INTEGER      NOT NULL DEFAULT 100
                    CHECK (max_score > 0 AND max_score <= 1000)
);

-- ----------------------------------------------------------------------------
-- 10. Варианты заданий.
-- ----------------------------------------------------------------------------
CREATE TABLE variants (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER      NOT NULL
                    REFERENCES tasks(id) ON DELETE CASCADE,
    number          INTEGER      NOT NULL CHECK (number > 0),
    description     TEXT         NOT NULL,
    UNIQUE (task_id, number)
);

-- ----------------------------------------------------------------------------
-- 11. Оценки (результат выполнения задания студентом).
-- ----------------------------------------------------------------------------
CREATE TABLE grades (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER      NOT NULL
                    REFERENCES students(id) ON DELETE CASCADE,
    task_id         INTEGER      NOT NULL
                    REFERENCES tasks(id) ON DELETE CASCADE,
    score           INTEGER      NOT NULL
                    CHECK (score >= 0 AND score <= 100),
    graded_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, task_id)
);

-- ----------------------------------------------------------------------------
-- Комментарии к таблицам — пригодятся в pgAdmin.
-- ----------------------------------------------------------------------------
COMMENT ON TABLE users        IS 'Учётные записи всех пользователей системы';
COMMENT ON TABLE employees    IS 'Сотрудники администрации';
COMMENT ON TABLE teachers     IS 'Преподавательский состав';
COMMENT ON TABLE students     IS 'Студенты';
COMMENT ON TABLE disciplines  IS 'Учебные дисциплины (предметы)';
COMMENT ON TABLE courses      IS 'Курсы — конкретные реализации дисциплин';
COMMENT ON TABLE enrollments  IS 'Запись студентов на курсы (M:N)';
COMMENT ON TABLE contracts    IS 'Договоры: об обучении (со студентом) или трудовой (с преподавателем)';
COMMENT ON TABLE tasks        IS 'Задания, выдаваемые в рамках курсов';
COMMENT ON TABLE variants     IS 'Варианты заданий';
COMMENT ON TABLE grades       IS 'Оценки студентов за задания';
