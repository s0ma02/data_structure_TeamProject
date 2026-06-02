from __future__ import annotations

import sqlite3
from collections import deque
from typing import Any


CourseMap = dict[str, dict[str, Any]]
PrerequisiteEdge = dict[str, Any]

_CURRENT_COURSES: CourseMap = {}
_CURRENT_PREREQUISITES: list[PrerequisiteEdge] = []


def load_courses(conn: sqlite3.Connection) -> CourseMap:
    """Load all courses as graph vertices."""
    cursor = conn.execute(
        """
        SELECT course_id, course_name, credit, category, sub_category,
               recommended_year, recommended_semester, is_offered, language, note
        FROM courses
        ORDER BY course_id
        """
    )
    rows = _dict_rows(cursor)
    courses = {row["course_id"]: row for row in rows}
    _set_current_courses(courses)
    return courses


def load_prerequisites(conn: sqlite3.Connection) -> list[PrerequisiteEdge]:
    """Load prerequisite rows as directed edges."""
    cursor = conn.execute(
        """
        SELECT id, from_course_id, to_course_id, relation_type, weight, reason
        FROM prerequisites
        ORDER BY from_course_id, to_course_id, relation_type
        """
    )
    prerequisites = _dict_rows(cursor)
    _set_current_prerequisites(prerequisites)
    return prerequisites


def build_adjacency_list(
    courses: CourseMap,
    prerequisites: list[PrerequisiteEdge],
) -> dict[str, list[PrerequisiteEdge]]:
    """Build outgoing edges: prerequisite course -> later courses."""
    adjacency = {course_id: [] for course_id in courses}
    for edge in prerequisites:
        adjacency.setdefault(edge["from_course_id"], []).append(edge)
        adjacency.setdefault(edge["to_course_id"], [])
    return _sort_edge_map(adjacency, "to_course_id")


def build_reverse_adjacency_list(
    courses: CourseMap,
    prerequisites: list[PrerequisiteEdge],
) -> dict[str, list[PrerequisiteEdge]]:
    """Build incoming edges: later course -> prerequisite courses."""
    reverse = {course_id: [] for course_id in courses}
    for edge in prerequisites:
        reverse.setdefault(edge["to_course_id"], []).append(edge)
        reverse.setdefault(edge["from_course_id"], [])
    return _sort_edge_map(reverse, "from_course_id")


def calculate_indegree(
    courses: CourseMap,
    prerequisites: list[PrerequisiteEdge],
) -> dict[str, int]:
    indegree = {course_id: 0 for course_id in courses}
    for edge in prerequisites:
        indegree.setdefault(edge["from_course_id"], 0)
        indegree[edge["to_course_id"]] = indegree.get(edge["to_course_id"], 0) + 1
    return indegree


def has_cycle(
    courses: CourseMap,
    prerequisites: list[PrerequisiteEdge],
) -> bool:
    try:
        topological_sort(courses, prerequisites)
    except ValueError:
        return True
    return False


def topological_sort(
    courses: CourseMap,
    prerequisites: list[PrerequisiteEdge],
) -> list[str]:
    """Return course IDs in a valid learning order."""
    adjacency = build_adjacency_list(courses, prerequisites)
    indegree = calculate_indegree(courses, prerequisites)
    queue = deque(sorted(course_id for course_id, degree in indegree.items() if degree == 0))
    order: list[str] = []

    while queue:
        course_id = queue.popleft()
        order.append(course_id)
        for edge in adjacency.get(course_id, []):
            next_course_id = edge["to_course_id"]
            indegree[next_course_id] -= 1
            if indegree[next_course_id] == 0:
                queue.append(next_course_id)
        queue = deque(sorted(queue))

    if len(order) != len(indegree):
        unresolved = sorted(course_id for course_id, degree in indegree.items() if degree > 0)
        raise ValueError(
            "Prerequisite graph contains a cycle. "
            f"Unresolved courses: {', '.join(unresolved)}"
        )
    return order


def get_direct_prerequisites(
    course_id: str,
    prerequisites: list[PrerequisiteEdge] | None = None,
) -> list[str]:
    """Return only immediate prerequisite course IDs for a course."""
    edges = _resolve_prerequisites(prerequisites)
    return sorted(
        edge["from_course_id"]
        for edge in edges
        if edge["to_course_id"] == course_id
    )


def get_all_prerequisites(
    course_id: str,
    prerequisites: list[PrerequisiteEdge] | None = None,
) -> list[str]:
    """Return direct and indirect prerequisite course IDs."""
    edges = _resolve_prerequisites(prerequisites)
    reverse = build_reverse_adjacency_list(_course_ids_from_edges(edges), edges)
    seen: set[str] = set()
    stack = [edge["from_course_id"] for edge in reverse.get(course_id, [])]

    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(edge["from_course_id"] for edge in reverse.get(current, []))

    return sorted(seen)


def get_next_courses(
    course_id: str,
    prerequisites: list[PrerequisiteEdge] | None = None,
) -> list[str]:
    """Return courses that directly depend on the given course."""
    edges = _resolve_prerequisites(prerequisites)
    return sorted(
        edge["to_course_id"]
        for edge in edges
        if edge["from_course_id"] == course_id
    )


def load_graph(conn: sqlite3.Connection) -> tuple[CourseMap, list[PrerequisiteEdge]]:
    """Convenience loader that refreshes the module-level lookup data."""
    courses = load_courses(conn)
    prerequisites = load_prerequisites(conn)
    return courses, prerequisites


def _set_current_courses(courses: CourseMap) -> None:
    global _CURRENT_COURSES
    _CURRENT_COURSES = courses


def _set_current_prerequisites(prerequisites: list[PrerequisiteEdge]) -> None:
    global _CURRENT_PREREQUISITES
    _CURRENT_PREREQUISITES = prerequisites


def _resolve_prerequisites(
    prerequisites: list[PrerequisiteEdge] | None,
) -> list[PrerequisiteEdge]:
    if prerequisites is not None:
        return prerequisites
    return _CURRENT_PREREQUISITES


def _sort_edge_map(
    edge_map: dict[str, list[PrerequisiteEdge]],
    sort_key: str,
) -> dict[str, list[PrerequisiteEdge]]:
    for course_id in edge_map:
        edge_map[course_id] = sorted(
            edge_map[course_id],
            key=lambda edge: (edge[sort_key], edge["relation_type"]),
        )
    return edge_map


def _course_ids_from_edges(prerequisites: list[PrerequisiteEdge]) -> CourseMap:
    courses: CourseMap = dict(_CURRENT_COURSES)
    for edge in prerequisites:
        courses.setdefault(edge["from_course_id"], {"course_id": edge["from_course_id"]})
        courses.setdefault(edge["to_course_id"], {"course_id": edge["to_course_id"]})
    return courses


def _dict_rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
