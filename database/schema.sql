PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    credit INTEGER NOT NULL CHECK (credit > 0),
    category TEXT NOT NULL,
    sub_category TEXT,
    recommended_year TEXT,
    recommended_semester TEXT,
    is_offered INTEGER DEFAULT 1 CHECK (is_offered IN (0, 1)),
    language TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS prerequisites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_course_id TEXT NOT NULL,
    to_course_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight INTEGER DEFAULT 3 CHECK (weight >= 1),
    reason TEXT,
    FOREIGN KEY (from_course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (to_course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    CHECK (from_course_id <> to_course_id),
    UNIQUE (from_course_id, to_course_id, relation_type)
);

CREATE TABLE IF NOT EXISTS requirements (
    requirement_id TEXT PRIMARY KEY,
    requirement_name TEXT NOT NULL,
    category TEXT NOT NULL,
    required_credits INTEGER CHECK (required_credits IS NULL OR required_credits >= 0),
    required_course_count INTEGER CHECK (required_course_count IS NULL OR required_course_count >= 0),
    description TEXT
);

CREATE TABLE IF NOT EXISTS requirement_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    is_mandatory INTEGER DEFAULT 1 CHECK (is_mandatory IN (0, 1)),
    FOREIGN KEY (requirement_id) REFERENCES requirements(requirement_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE (requirement_id, course_id)
);

CREATE TABLE IF NOT EXISTS choice_groups (
    choice_group_id TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL,
    group_name TEXT NOT NULL,
    required_select_count INTEGER NOT NULL CHECK (required_select_count > 0),
    description TEXT,
    FOREIGN KEY (requirement_id) REFERENCES requirements(requirement_id) ON DELETE CASCADE,
    UNIQUE (requirement_id, group_name)
);

CREATE TABLE IF NOT EXISTS choice_group_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    choice_group_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    FOREIGN KEY (choice_group_id) REFERENCES choice_groups(choice_group_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE (choice_group_id, course_id)
);

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    student_name TEXT,
    current_year INTEGER CHECK (current_year IS NULL OR current_year BETWEEN 1 AND 6),
    current_semester INTEGER CHECK (current_semester IS NULL OR current_semester BETWEEN 1 AND 2),
    target_track TEXT
);

CREATE TABLE IF NOT EXISTS completed_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    completed_year INTEGER,
    completed_semester INTEGER CHECK (completed_semester IS NULL OR completed_semester BETWEEN 1 AND 2),
    grade TEXT,
    score INTEGER CHECK (score IS NULL OR score BETWEEN 0 AND 100),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE RESTRICT,
    UNIQUE (student_id, course_id)
);

CREATE TABLE IF NOT EXISTS non_course_requirements (
    requirement_id TEXT PRIMARY KEY,
    requirement_name TEXT NOT NULL,
    required_count INTEGER NOT NULL CHECK (required_count > 0),
    recommended_timing TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS student_non_course_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    completed_count INTEGER DEFAULT 0 CHECK (completed_count >= 0),
    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
    note TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (requirement_id) REFERENCES non_course_requirements(requirement_id) ON DELETE CASCADE,
    UNIQUE (student_id, requirement_id)
);

CREATE INDEX IF NOT EXISTS idx_courses_category ON courses(category, sub_category);
CREATE INDEX IF NOT EXISTS idx_prerequisites_from ON prerequisites(from_course_id);
CREATE INDEX IF NOT EXISTS idx_prerequisites_to ON prerequisites(to_course_id);
CREATE INDEX IF NOT EXISTS idx_requirement_courses_requirement ON requirement_courses(requirement_id);
CREATE INDEX IF NOT EXISTS idx_choice_group_courses_group ON choice_group_courses(choice_group_id);
CREATE INDEX IF NOT EXISTS idx_completed_courses_student ON completed_courses(student_id);
CREATE INDEX IF NOT EXISTS idx_student_non_course_records_student ON student_non_course_records(student_id);
