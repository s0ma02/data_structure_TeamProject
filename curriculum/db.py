from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "curriculum.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "database" / "seed.sql"


def connect(
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    check_same_thread: bool = True,
) -> sqlite3.Connection:
    conn = sqlite3.connect(Path(db_path), check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_student_non_course_record_columns(conn)
    return conn


def initialize_database(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()
    return db_path


def initialize_memory_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def _ensure_student_non_course_record_columns(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(student_non_course_records)"
        ).fetchall()
    }
    if not columns:
        return

    changed = False
    if "completed" not in columns:
        conn.execute(
            """
            ALTER TABLE student_non_course_records
            ADD COLUMN completed INTEGER NOT NULL DEFAULT 0
            CHECK (completed IN (0, 1))
            """
        )
        changed = True
    if "note" not in columns:
        conn.execute("ALTER TABLE student_non_course_records ADD COLUMN note TEXT")
        changed = True
    if changed:
        conn.commit()
