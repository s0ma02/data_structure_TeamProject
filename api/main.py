from __future__ import annotations

from collections.abc import Iterator
import sqlite3
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from curriculum.db import DEFAULT_DB_PATH, connect, initialize_database
from curriculum.graph import (
    get_direct_prerequisites,
    get_next_courses,
    has_cycle,
    load_graph,
)
from curriculum.recommender import CurriculumRecommender
from curriculum.requirements import RequirementChecker


app = FastAPI(title="Curriculum Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompletedCoursesUpdate(BaseModel):
    course_ids: list[str] = Field(default_factory=list)


# Keep this payload aligned with the React profile form and simple API demos.
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    current_year: Optional[int] = None
    current_semester: Optional[int] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    track: Optional[str] = None


class NonCourseRequirementUpdate(BaseModel):
    key: str
    completed: bool = False
    value: int = Field(default=0, ge=0)
    note: Optional[str] = ""


class NonCourseRequirementsUpdate(BaseModel):
    items: list[NonCourseRequirementUpdate] = Field(default_factory=list)


SAMPLE_STUDENT_ID = "S001"
SAMPLE_COMPLETED_COURSES = ("COM2002", "COM2003")
SAMPLE_STUDENT_NAME = "Sample Student"
SAMPLE_CURRENT_YEAR = 1
SAMPLE_CURRENT_SEMESTER = 2
SAMPLE_TARGET_TRACK = "COMMON"
ALLOWED_TRACKS = {"COMMON", "PROFESSIONAL", "TEACHER"}


def get_db() -> Iterator[sqlite3.Connection]:
    if not DEFAULT_DB_PATH.exists():
        initialize_database(DEFAULT_DB_PATH)
    conn = connect(DEFAULT_DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/api/courses")
def get_courses(conn: sqlite3.Connection = Depends(get_db)) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT course_id, course_name, credit, category, sub_category,
               recommended_year, recommended_semester, is_offered, language, note
        FROM courses
        ORDER BY course_id
        """
    ).fetchall()
    return [_course_response(row) for row in rows]


@app.get("/api/students/{student_id}")
def get_student(
    student_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    return _student_response(_get_student_or_404(conn, student_id))


@app.put("/api/students/{student_id}")
def update_student(
    student_id: str,
    payload: StudentUpdate,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    _get_student_or_404(conn, student_id)
    # Profile fields affect recommendation scoring, so validate them before saving.
    name, current_year, current_semester, target_track = _validated_student_update(
        payload
    )

    try:
        conn.execute(
            """
            UPDATE students
            SET student_name = ?,
                current_year = ?,
                current_semester = ?,
                target_track = ?
            WHERE student_id = ?
            """,
            (name, current_year, current_semester, target_track, student_id),
        )
        conn.commit()
    except sqlite3.DatabaseError:
        conn.rollback()
        raise

    return _student_response(_get_student_or_404(conn, student_id))


@app.get("/api/students/{student_id}/completed")
def get_completed_courses(
    student_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    _get_student_or_404(conn, student_id)
    return RequirementChecker(conn).get_completed_courses(student_id)


@app.post("/api/students/{student_id}/reset-sample")
def reset_sample_student(
    student_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    if student_id != SAMPLE_STUDENT_ID:
        raise HTTPException(
            status_code=400,
            detail=f"Sample reset is only available for {SAMPLE_STUDENT_ID}",
        )
    _reset_sample_student(conn)
    completed_courses = RequirementChecker(conn).get_completed_courses(student_id)
    return {
        "student_id": student_id,
        "student": _student_response(_get_student_or_404(conn, student_id)),
        "completed_course_ids": [course["course_id"] for course in completed_courses],
        "completed_courses": completed_courses,
        "non_course_requirements": _non_course_requirements_response(student_id, conn)[
            "items"
        ],
    }


@app.get("/api/students/{student_id}/requirements")
def get_requirements(
    student_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    _get_student_or_404(conn, student_id)
    summary = RequirementChecker(conn).get_requirement_summary(student_id)
    return _requirements_response(student_id, summary)


@app.get("/api/students/{student_id}/non-course-requirements")
def get_non_course_requirements(
    student_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    _get_student_or_404(conn, student_id)
    return _non_course_requirements_response(student_id, conn)


@app.put("/api/students/{student_id}/non-course-requirements")
def update_non_course_requirements(
    student_id: str,
    payload: NonCourseRequirementsUpdate,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    _get_student_or_404(conn, student_id)
    definitions = _non_course_requirement_definitions(conn)
    requested_items = _dedupe_non_course_items(payload.items)
    missing = sorted(key for key in requested_items if key not in definitions)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown non-course requirement: {', '.join(missing)}",
        )

    try:
        for key, item in requested_items.items():
            required_count = definitions[key]["required_count"]
            value = max(item.value, 0)
            completed = item.completed or value >= required_count
            stored_value = max(value, required_count) if completed else value
            conn.execute(
                """
                INSERT INTO student_non_course_records (
                    student_id, requirement_id, completed_count, completed, note
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id, requirement_id) DO UPDATE SET
                    completed_count = excluded.completed_count,
                    completed = excluded.completed,
                    note = excluded.note
                """,
                (
                    student_id,
                    key,
                    stored_value,
                    1 if completed else 0,
                    (item.note or "").strip(),
                ),
            )
        conn.commit()
    except sqlite3.DatabaseError:
        conn.rollback()
        raise

    return _non_course_requirements_response(student_id, conn)


@app.put("/api/students/{student_id}/completed")
def update_completed_courses(
    student_id: str,
    payload: CompletedCoursesUpdate,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    student = _get_student_or_404(conn, student_id)
    course_ids = _dedupe_course_ids(payload.course_ids)
    _ensure_courses_exist(conn, course_ids)

    existing = {
        row["course_id"]: dict(row)
        for row in conn.execute(
            """
            SELECT course_id, completed_year, completed_semester, grade, score
            FROM completed_courses
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchall()
    }

    try:
        conn.execute("DELETE FROM completed_courses WHERE student_id = ?", (student_id,))
        for course_id in course_ids:
            completed = existing.get(course_id, {})
            conn.execute(
                """
                INSERT INTO completed_courses (
                    student_id, course_id, completed_year, completed_semester, grade, score
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    course_id,
                    completed.get("completed_year", student["current_year"]),
                    completed.get("completed_semester", student["current_semester"]),
                    completed.get("grade", "P"),
                    completed.get("score"),
                ),
            )
        conn.commit()
    except sqlite3.DatabaseError:
        conn.rollback()
        raise

    completed_courses = RequirementChecker(conn).get_completed_courses(student_id)
    return {
        "student_id": student_id,
        "completed_course_ids": [course["course_id"] for course in completed_courses],
        "completed_courses": completed_courses,
    }


@app.get("/api/students/{student_id}/recommendations")
def get_recommendations(
    student_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    _get_student_or_404(conn, student_id)
    try:
        return CurriculumRecommender(conn).recommend_next_courses(student_id, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/graph")
def get_graph(conn: sqlite3.Connection = Depends(get_db)) -> dict[str, Any]:
    courses, prerequisites = load_graph(conn)
    return {
        "nodes": [
            _graph_node_response(course)
            for course in sorted(courses.values(), key=lambda item: item["course_id"])
        ],
        "edges": [_graph_edge_response(edge) for edge in prerequisites],
        "is_dag": not has_cycle(courses, prerequisites),
    }


@app.get("/api/courses/{course_id}/prerequisites")
def get_course_prerequisites(
    course_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    courses, prerequisites = load_graph(conn)
    course = courses.get(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Unknown course_id: {course_id}")

    direct_prerequisite_ids = get_direct_prerequisites(course_id, prerequisites)
    dependent_ids = get_next_courses(course_id, prerequisites)
    return {
        "course_id": course_id,
        "name": course["course_name"],
        "credits": course["credit"],
        "category": _category_key(course.get("category")),
        "recommended_year": _first_number(course.get("recommended_year")),
        "recommended_semester": _first_number(course.get("recommended_semester")),
        "recommended_year_label": course.get("recommended_year"),
        "recommended_semester_label": course.get("recommended_semester"),
        "prerequisites": [
            _course_relation_response(courses[prerequisite_id])
            for prerequisite_id in direct_prerequisite_ids
            if prerequisite_id in courses
        ],
        "dependents": [
            _course_relation_response(courses[dependent_id])
            for dependent_id in dependent_ids
            if dependent_id in courses
        ],
    }


def _get_student_or_404(conn: sqlite3.Connection, student_id: str) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT student_id, student_name, current_year, current_semester, target_track
        FROM students
        WHERE student_id = ?
        """,
        (student_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown student_id: {student_id}")
    return dict(row)


def _validated_student_update(
    payload: StudentUpdate,
) -> tuple[str, int, int, str]:
    name = (payload.name or "").strip()
    current_year = (
        payload.current_year
        if payload.current_year is not None
        else payload.year
    )
    current_semester = (
        payload.current_semester
        if payload.current_semester is not None
        else payload.semester
    )
    target_track = (payload.track or "").strip().upper()

    if not name:
        raise HTTPException(status_code=400, detail="Student name is required.")
    if current_year not in {1, 2, 3, 4}:
        raise HTTPException(
            status_code=400,
            detail="current_year must be one of 1, 2, 3, or 4.",
        )
    if current_semester not in {1, 2}:
        raise HTTPException(
            status_code=400,
            detail="current_semester must be one of 1 or 2.",
        )
    if target_track not in ALLOWED_TRACKS:
        raise HTTPException(
            status_code=400,
            detail=f"track must be one of {', '.join(sorted(ALLOWED_TRACKS))}.",
        )

    return name, current_year, current_semester, target_track


def _ensure_courses_exist(conn: sqlite3.Connection, course_ids: list[str]) -> None:
    if not course_ids:
        return
    placeholders = ",".join("?" for _ in course_ids)
    rows = conn.execute(
        f"SELECT course_id FROM courses WHERE course_id IN ({placeholders})",
        course_ids,
    ).fetchall()
    existing = {row["course_id"] for row in rows}
    missing = sorted(set(course_ids) - existing)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown course_id: {', '.join(missing)}",
        )


def _reset_sample_student(conn: sqlite3.Connection) -> None:
    try:
        conn.execute(
            """
            INSERT INTO students (
                student_id, student_name, current_year, current_semester, target_track
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                student_name = excluded.student_name,
                current_year = excluded.current_year,
                current_semester = excluded.current_semester,
                target_track = excluded.target_track
            """,
            (
                SAMPLE_STUDENT_ID,
                SAMPLE_STUDENT_NAME,
                SAMPLE_CURRENT_YEAR,
                SAMPLE_CURRENT_SEMESTER,
                SAMPLE_TARGET_TRACK,
            ),
        )
        conn.execute(
            "DELETE FROM completed_courses WHERE student_id = ?",
            (SAMPLE_STUDENT_ID,),
        )
        for course_id in SAMPLE_COMPLETED_COURSES:
            conn.execute(
                """
                INSERT INTO completed_courses (
                    student_id, course_id, completed_year, completed_semester, grade, score
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (SAMPLE_STUDENT_ID, course_id, 2026, 1, "P", None),
            )

        conn.execute(
            "DELETE FROM student_non_course_records WHERE student_id = ?",
            (SAMPLE_STUDENT_ID,),
        )
        requirement_rows = conn.execute(
            """
            SELECT requirement_id, required_count
            FROM non_course_requirements
            ORDER BY requirement_id
            """
        ).fetchall()
        for row in requirement_rows:
            conn.execute(
                """
                INSERT INTO student_non_course_records (
                    student_id, requirement_id, completed_count, completed, note
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    SAMPLE_STUDENT_ID,
                    row["requirement_id"],
                    row["required_count"],
                    1,
                    "",
                ),
            )
        conn.commit()
    except sqlite3.DatabaseError:
        conn.rollback()
        raise


def _dedupe_course_ids(course_ids: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for course_id in course_ids:
        normalized = course_id.strip()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _requirements_response(
    student_id: str,
    requirement_summary: dict[str, Any],
) -> dict[str, Any]:
    summary_items = [
        _course_requirement_response(requirement)
        for requirement in requirement_summary["course_requirements"]
    ]
    summary_items.extend(
        _non_course_requirement_response(requirement)
        for requirement in requirement_summary["non_course_requirements"]
    )
    return {
        "student_id": student_id,
        "summary": summary_items,
        "missing_courses": _missing_course_responses(
            requirement_summary["course_requirements"]
        ),
        "course_requirements_satisfied": requirement_summary[
            "course_requirements_satisfied"
        ],
        "non_course_requirements_satisfied": requirement_summary[
            "non_course_requirements_satisfied"
        ],
    }


def _course_requirement_response(requirement: dict[str, Any]) -> dict[str, Any]:
    if requirement["required_course_count"] is not None:
        completed = requirement["completed_course_count"]
        required = requirement["required_course_count"]
        unit = "과목"
    else:
        completed = requirement["completed_credits"]
        required = requirement["required_credits"] or 0
        unit = "학점"

    return {
        "requirement_id": requirement["requirement_id"],
        "name": requirement["requirement_name"],
        "category": _category_key(requirement["category"]),
        "type": "course",
        "status": _status(requirement["satisfied"]),
        "satisfied": requirement["satisfied"],
        "completed": completed,
        "required": required,
        "unit": unit,
        "progress_percent": _progress_percent(completed, required),
        "description": requirement["description"],
    }


def _non_course_requirement_response(requirement: dict[str, Any]) -> dict[str, Any]:
    completed = requirement["completed_count"]
    required = requirement["required_count"]
    return {
        "requirement_id": requirement["requirement_id"],
        "name": requirement["requirement_name"],
        "category": "non_course",
        "type": "non_course",
        "status": _status(requirement["satisfied"]),
        "satisfied": requirement["satisfied"],
        "completed": completed,
        "required": required,
        "unit": _non_course_unit(requirement["requirement_name"]),
        "progress_percent": _progress_percent(completed, required),
        "description": requirement["description"],
        "note": requirement.get("note", ""),
    }


def _non_course_requirements_response(
    student_id: str,
    conn: sqlite3.Connection,
) -> dict[str, Any]:
    return {
        "student_id": student_id,
        "items": [
            _non_course_requirement_item_response(requirement)
            for requirement in RequirementChecker(conn).check_non_course_requirements(
                student_id
            )
        ],
    }


def _non_course_requirement_item_response(
    requirement: dict[str, Any],
) -> dict[str, Any]:
    return {
        "key": requirement["requirement_id"],
        "name": requirement["requirement_name"],
        "completed": requirement["completed"],
        "value": requirement["completed_count"],
        "required_value": requirement["required_count"],
        "unit": _non_course_unit(requirement["requirement_name"]),
        "note": requirement.get("note", ""),
        "description": requirement.get("description"),
        "recommended_timing": requirement.get("recommended_timing"),
    }


def _non_course_requirement_definitions(
    conn: sqlite3.Connection,
) -> dict[str, dict[str, Any]]:
    return {
        row["requirement_id"]: dict(row)
        for row in conn.execute(
            """
            SELECT requirement_id, requirement_name, required_count
            FROM non_course_requirements
            """
        ).fetchall()
    }


def _dedupe_non_course_items(
    items: list[NonCourseRequirementUpdate],
) -> dict[str, NonCourseRequirementUpdate]:
    result: dict[str, NonCourseRequirementUpdate] = {}
    for item in items:
        key = item.key.strip()
        if key:
            result[key] = item.copy(update={"key": key})
    return result


def _non_course_unit(requirement_name: str | None) -> str:
    if requirement_name and "봉사" in requirement_name:
        return "시간"
    return "회"


def _missing_course_responses(
    course_requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    missing_by_id: dict[str, dict[str, Any]] = {}
    for requirement in course_requirements:
        if requirement["satisfied"]:
            continue
        candidates = []
        candidates.extend(requirement.get("missing_courses", []))
        for group in requirement.get("choice_groups", []):
            if not group["satisfied"]:
                candidates.extend(group.get("missing_options", []))
        candidates.extend(requirement.get("candidate_courses", []))

        for course in candidates:
            course_id = course["course_id"]
            item = missing_by_id.setdefault(
                course_id,
                {
                    "course_id": course_id,
                    "name": course["course_name"],
                    "category": _category_key(course.get("category")),
                    "requirement_names": [],
                },
            )
            requirement_name = requirement["requirement_name"]
            if requirement_name not in item["requirement_names"]:
                item["requirement_names"].append(requirement_name)

    return sorted(missing_by_id.values(), key=lambda item: item["course_id"])


def _progress_percent(completed: int, required: int) -> int:
    if required <= 0:
        return 100
    return min(round((completed / required) * 100), 100)


def _status(satisfied: bool) -> str:
    return "충족" if satisfied else "부족"


def _category_key(category: str | None) -> str:
    if category == "MAJOR":
        return "major"
    if category == "TEACHING":
        return "teaching"
    return "non_course"


def _graph_node_response(course: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": course["course_id"],
        "label": course["course_name"],
        "course_id": course["course_id"],
        "name": course["course_name"],
        "category": _category_key(course.get("category")),
        "sub_category": course.get("sub_category"),
        "recommended_year": _first_number(course.get("recommended_year")),
        "recommended_semester": _first_number(course.get("recommended_semester")),
        "recommended_year_label": course.get("recommended_year"),
        "recommended_semester_label": course.get("recommended_semester"),
        "credits": course["credit"],
        "is_offered": bool(course.get("is_offered")),
        "language": course.get("language"),
        "note": course.get("note"),
    }


def _graph_edge_response(edge: dict[str, Any]) -> dict[str, Any]:
    relation_type = edge["relation_type"].lower()
    return {
        "id": f"{edge['from_course_id']}-{edge['to_course_id']}-{relation_type}",
        "source": edge["from_course_id"],
        "target": edge["to_course_id"],
        "relation_type": edge["relation_type"],
        "weight": edge["weight"],
        "reason": edge["reason"],
    }


def _course_relation_response(course: dict[str, Any]) -> dict[str, Any]:
    return {
        "course_id": course["course_id"],
        "name": course["course_name"],
        "credits": course["credit"],
        "category": _category_key(course.get("category")),
    }


def _first_number(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = ""
    for char in value:
        if char.isdigit():
            digits += char
        elif digits:
            break
    return int(digits) if digits else None


def _course_response(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["is_offered"] = bool(item["is_offered"])
    return item


def _student_response(student: dict[str, Any]) -> dict[str, Any]:
    return {
        "student_id": student["student_id"],
        "student_name": student["student_name"],
        "current_year": student["current_year"],
        "current_semester": student["current_semester"],
        "target_track": student["target_track"],
    }
