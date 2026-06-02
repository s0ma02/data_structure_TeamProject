from __future__ import annotations

import argparse
import sys
from pathlib import Path

from curriculum.db import DEFAULT_DB_PATH, connect, initialize_database
from curriculum.graph import (
    get_all_prerequisites,
    get_direct_prerequisites,
    get_next_courses,
    has_cycle,
    load_graph,
    topological_sort,
)
from curriculum.recommender import CurriculumRecommender
from curriculum.requirements import RequirementChecker


def open_database(db_path: str | Path):
    path = Path(db_path)
    if not path.exists():
        initialize_database(path)
    return connect(path)


def cmd_init_db(args: argparse.Namespace) -> int:
    path = initialize_database(args.db)
    print(f"Initialized database: {path}")
    return 0


def cmd_list_courses(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        rows = conn.execute(
            """
            SELECT course_id, course_name, credit, category, sub_category,
                   recommended_year, recommended_semester, is_offered
            FROM courses
            ORDER BY course_id
            """
        ).fetchall()
    for row in rows:
        offered = "offered" if row["is_offered"] else "not offered"
        timing = _timing(row["recommended_year"], row["recommended_semester"])
        print(
            f"{row['course_id']:18} {row['course_name']} "
            f"({row['credit']}cr, {row['category']}, {row['sub_category']}, {timing}, {offered})"
        )
    print(f"Total courses: {len(rows)}")
    return 0


def cmd_completed(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        checker = RequirementChecker(conn)
        courses = checker.get_completed_courses(args.student_id)
    print(f"Completed courses for {args.student_id}")
    if not courses:
        print("  None")
        return 0
    for course in courses:
        print(
            f"  {course['course_id']} {course['course_name']} "
            f"({course['credit']}cr, {course['completed_year']}-{course['completed_semester']})"
        )
    return 0


def cmd_requirements(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        summary = RequirementChecker(conn).get_requirement_summary(args.student_id)
    student = summary["student"]
    print(
        f"Student: {student['student_id']} {student['student_name']} "
        f"({student['current_year']}Y {student['current_semester']}S, {student['target_track']})"
    )
    print("Course requirements")
    for requirement in summary["course_requirements"]:
        _print_requirement(requirement)
    print("Non-course requirements")
    for requirement in summary["non_course_requirements"]:
        print(
            f"  [{_ok(requirement['satisfied'])}] {requirement['requirement_name']}: "
            f"{requirement['completed_count']}/{requirement['required_count']} "
            f"({requirement['recommended_timing']})"
        )
    return 0


def cmd_non_course_status(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        statuses = RequirementChecker(conn).check_non_course_requirements(args.student_id)
    print(f"Non-course requirements for {args.student_id}")
    for status in statuses:
        print(
            f"  [{_ok(status['satisfied'])}] {status['requirement_name']}: "
            f"{status['completed_count']}/{status['required_count']}, "
            f"missing {status['missing_count']}"
        )
    return 0


def cmd_check_dag(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        courses, prerequisites = load_graph(conn)
        cyclic = has_cycle(courses, prerequisites)
    print(f"Total courses: {len(courses)}")
    print(f"Total prerequisite edges: {len(prerequisites)}")
    print(f"Valid DAG: {not cyclic}")
    return 0 if not cyclic else 1


def cmd_topo(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        courses, prerequisites = load_graph(conn)
        order = topological_sort(courses, prerequisites)
    print("Topological order preview:")
    print(", ".join(order[: args.limit]))
    print(f"Total ordered courses: {len(order)}")
    return 0


def cmd_prereq(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        courses, prerequisites = load_graph(conn)
        course = courses.get(args.course_id)
        if course is None:
            raise ValueError(f"Unknown course_id: {args.course_id}")
        direct = get_direct_prerequisites(args.course_id, prerequisites)
        all_prereq = get_all_prerequisites(args.course_id, prerequisites)
        next_courses = get_next_courses(args.course_id, prerequisites)

    print(f"Course: {args.course_id} {course['course_name']}")
    print(f"Direct prerequisites: {_join_or_none(direct)}")
    print(f"All prerequisites: {_join_or_none(all_prereq)}")
    print(f"Next courses: {_join_or_none(next_courses)}")
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        recommendations = CurriculumRecommender(conn).recommend_next_courses(
            args.student_id,
            args.limit,
        )
    _print_recommendations(args.student_id, recommendations)
    return 0


def cmd_recommend_semester(args: argparse.Namespace) -> int:
    with open_database(args.db) as conn:
        recommendations = CurriculumRecommender(conn).recommend_by_year_and_semester(
            args.student_id,
            args.year,
            args.semester,
            args.limit,
        )
    _print_recommendations(args.student_id, recommendations)
    return 0


def _print_requirement(requirement: dict) -> None:
    required_credits = requirement["required_credits"]
    required_count = requirement["required_course_count"]
    print(
        f"  [{_ok(requirement['satisfied'])}] {requirement['requirement_name']}: "
        f"credits {requirement['completed_credits']}/{required_credits if required_credits is not None else '-'}, "
        f"courses {requirement['completed_course_count']}/{required_count if required_count is not None else '-'}"
    )
    if requirement.get("missing_courses"):
        missing = ", ".join(
            f"{course['course_id']} {course['course_name']}"
            for course in requirement["missing_courses"]
        )
        print(f"      missing courses: {missing}")
    for group in requirement.get("choice_groups", []):
        print(
            f"      choice group [{_ok(group['satisfied'])}] {group['group_name']}: "
            f"{group['completed_select_count']}/{group['required_select_count']}"
        )
        if not group["satisfied"]:
            options = ", ".join(
                f"{course['course_id']} {course['course_name']}"
                for course in group["missing_options"]
            )
            print(f"        remaining options: {options}")


def _print_recommendations(student_id: str, recommendations: list[dict]) -> None:
    print(f"Recommendations for {student_id}")
    if not recommendations:
        print("  No eligible courses.")
        return
    for index, item in enumerate(recommendations, start=1):
        print(
            f"{index:2}. {item['course_id']} {item['course_name']} "
            f"({item['credit']}cr, score {item['score']}, "
            f"{_timing(item['recommended_year'], item['recommended_semester'])})"
        )
        print(f"    reasons: {', '.join(item['reasons'])}")
        print(f"    requirement relevance: {_join_or_none(item['requirement_relevance'])}")
        print(
            "    prerequisites: "
            f"required missing={_join_or_none(item['missing_required_prerequisites'])}; "
            f"recommended completed={_join_or_none(item['completed_recommended_prerequisites'])}; "
            f"recommended missing={_join_or_none(item['missing_recommended_prerequisites'])}"
        )


def _ok(value: bool) -> str:
    return "OK" if value else "NO"


def _join_or_none(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _timing(year: str | None, semester: str | None) -> str:
    if year and semester:
        return f"{year}Y/{semester}S"
    if year:
        return f"{year}Y"
    if semester:
        return f"{semester}S"
    return "-"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curriculum Recommendation System")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db")
    init_db.set_defaults(func=cmd_init_db)

    list_courses = subparsers.add_parser("list-courses")
    list_courses.set_defaults(func=cmd_list_courses)

    requirements = subparsers.add_parser("requirements")
    requirements.add_argument("student_id", nargs="?", default="S001")
    requirements.set_defaults(func=cmd_requirements)

    non_course = subparsers.add_parser("non-course-status")
    non_course.add_argument("student_id", nargs="?", default="S001")
    non_course.set_defaults(func=cmd_non_course_status)

    completed = subparsers.add_parser("completed")
    completed.add_argument("student_id", nargs="?", default="S001")
    completed.set_defaults(func=cmd_completed)

    check_dag = subparsers.add_parser("check-dag")
    check_dag.set_defaults(func=cmd_check_dag)

    topo = subparsers.add_parser("topo")
    topo.add_argument("--limit", type=int, default=20)
    topo.set_defaults(func=cmd_topo)

    prereq = subparsers.add_parser("prereq")
    prereq.add_argument("course_id")
    prereq.set_defaults(func=cmd_prereq)

    recommend = subparsers.add_parser("recommend")
    recommend.add_argument("student_id", nargs="?", default="S001")
    recommend.add_argument("--limit", type=int, default=10)
    recommend.set_defaults(func=cmd_recommend)

    recommend_semester = subparsers.add_parser("recommend-semester")
    recommend_semester.add_argument("student_id", nargs="?", default="S001")
    recommend_semester.add_argument("--year", type=int, required=True)
    recommend_semester.add_argument("--semester", type=int, required=True, choices=[1, 2])
    recommend_semester.add_argument("--limit", type=int, default=10)
    recommend_semester.set_defaults(func=cmd_recommend_semester)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
