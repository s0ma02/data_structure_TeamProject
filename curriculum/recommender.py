from __future__ import annotations

import sqlite3
from typing import Any

from .graph import has_cycle, load_graph
from .requirements import RequirementChecker


class CurriculumRecommender:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.requirements = RequirementChecker(conn)

    def recommend_next_courses(self, student_id: str, limit: int = 10) -> list[dict[str, Any]]:
        student = self._student(student_id)
        return self._recommend(
            student_id,
            limit=limit,
            year=student["current_year"],
            semester=student["current_semester"],
        )

    def recommend_by_year_and_semester(
        self,
        student_id: str,
        year: int,
        semester: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._recommend(student_id, limit=limit, year=year, semester=semester)

    def recommend_required_courses_first(
        self,
        student_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        recommendations = self.recommend_next_courses(student_id, limit=1000)
        recommendations.sort(
            key=lambda item: (
                not bool(item["requirement_relevance"]),
                -item["score"],
                item["course_id"],
            )
        )
        return recommendations[:limit]

    def recommend_track_courses(
        self,
        student_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        student = self._student(student_id)
        recommendations = [
            item
            for item in self.recommend_next_courses(student_id, limit=1000)
            if self._matches_track(item, student["target_track"])
        ]
        return recommendations[:limit]

    def explain_recommendation(
        self,
        student_id: str,
        course_id: str,
    ) -> dict[str, Any]:
        student = self._student(student_id)
        course = self._course(course_id)
        completed_ids = self._completed_course_ids(student_id)
        required_edges = self._incoming_edges(course_id, "REQUIRED")
        recommended_edges = self._incoming_edges(course_id, "RECOMMENDED")
        missing_required = [
            edge["from_course_id"]
            for edge in required_edges
            if edge["from_course_id"] not in completed_ids
        ]
        completed_recommended = [
            edge["from_course_id"]
            for edge in recommended_edges
            if edge["from_course_id"] in completed_ids
        ]
        missing_recommended = [
            edge["from_course_id"]
            for edge in recommended_edges
            if edge["from_course_id"] not in completed_ids
        ]
        recommendation = self._score_course(
            student_id=student_id,
            student=student,
            course=course,
            completed_recommended=completed_recommended,
            missing_recommended=missing_recommended,
            year=student["current_year"],
            semester=student["current_semester"],
        )
        recommendation["missing_required_prerequisites"] = missing_required
        recommendation["eligible"] = (
            course_id not in completed_ids
            and not missing_required
            and bool(course["is_offered"])
            and self._valid_dag()
        )
        return recommendation

    def _recommend(
        self,
        student_id: str,
        limit: int,
        year: int | None,
        semester: int | None,
    ) -> list[dict[str, Any]]:
        if not self._valid_dag():
            raise ValueError("Prerequisite graph is not a valid DAG.")

        student = self._student(student_id)
        completed_ids = self._completed_course_ids(student_id)
        recommendations: list[dict[str, Any]] = []
        for course in self._offered_courses():
            if course["course_id"] in completed_ids:
                continue
            required_edges = self._incoming_edges(course["course_id"], "REQUIRED")
            missing_required = [
                edge["from_course_id"]
                for edge in required_edges
                if edge["from_course_id"] not in completed_ids
            ]
            if missing_required:
                continue

            recommended_edges = self._incoming_edges(course["course_id"], "RECOMMENDED")
            completed_recommended = [
                edge["from_course_id"]
                for edge in recommended_edges
                if edge["from_course_id"] in completed_ids
            ]
            missing_recommended = [
                edge["from_course_id"]
                for edge in recommended_edges
                if edge["from_course_id"] not in completed_ids
            ]
            recommendation = self._score_course(
                student_id=student_id,
                student=student,
                course=course,
                completed_recommended=completed_recommended,
                missing_recommended=missing_recommended,
                year=year,
                semester=semester,
            )
            recommendation["missing_required_prerequisites"] = []
            recommendations.append(recommendation)

        recommendations.sort(key=lambda item: (-item["score"], item["course_id"]))
        return recommendations[:limit]

    def _score_course(
        self,
        student_id: str,
        student: dict[str, Any],
        course: dict[str, Any],
        completed_recommended: list[str],
        missing_recommended: list[str],
        year: int | None,
        semester: int | None,
    ) -> dict[str, Any]:
        score = 0
        reasons: list[str] = []
        relevance = self._requirement_relevance(student_id, course)

        if relevance:
            score += 40
            reasons.append("미충족 졸업/교직 요건에 직접 기여")

        score += 30
        reasons.append("필수 선수과목 충족")

        years = _parse_numbers(course["recommended_year"])
        if year is not None and year in years:
            score += 15
            reasons.append(f"{year}학년 권장 과목")
        elif year is not None and years and min(years) - year >= 2:
            score -= 20
            reasons.append("현재 학년보다 많이 뒤의 권장 과목")

        semesters = _parse_numbers(course["recommended_semester"])
        if semester is not None and semester in semesters:
            score += 10
            reasons.append(f"{semester}학기 권장 과목")

        if self._matches_track(course, student["target_track"]):
            score += 10
            reasons.append(f"{student['target_track']} 트랙과 관련")

        if completed_recommended:
            score += 5 * len(completed_recommended)
            reasons.append("권장 선수과목 일부 이수")
        if missing_recommended:
            reasons.append("미이수 권장 선수과목 있음")

        if not course["is_offered"]:
            score -= 30
            reasons.append("현재 미개설 과목")

        return {
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "credit": course["credit"],
            "category": course["category"],
            "sub_category": course["sub_category"],
            "recommended_year": course["recommended_year"],
            "recommended_semester": course["recommended_semester"],
            "score": score,
            "reasons": reasons,
            "missing_required_prerequisites": [],
            "completed_recommended_prerequisites": completed_recommended,
            "missing_recommended_prerequisites": missing_recommended,
            "requirement_relevance": relevance,
        }

    def _requirement_relevance(
        self,
        student_id: str,
        course: dict[str, Any],
    ) -> list[str]:
        relevance = self.requirements.requirement_relevance_for_course(
            student_id,
            course["course_id"],
        )
        summary = self.requirements.get_requirement_summary(student_id)
        unmet_by_id = {
            requirement["requirement_id"]: requirement
            for requirement in summary["course_requirements"]
            if not requirement["satisfied"]
        }
        if course["category"] == "MAJOR" and "MAJOR_CREDITS" in unmet_by_id:
            relevance.append(unmet_by_id["MAJOR_CREDITS"]["requirement_name"])
        if course["category"] == "TEACHING" and "TEACHING_CREDITS" in unmet_by_id:
            relevance.append(unmet_by_id["TEACHING_CREDITS"]["requirement_name"])
        return sorted(set(relevance))

    def _valid_dag(self) -> bool:
        courses, prerequisites = load_graph(self.conn)
        return not has_cycle(courses, prerequisites)

    def _student(self, student_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT student_id, student_name, current_year, current_semester, target_track
            FROM students
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown student_id: {student_id}")
        return dict(row)

    def _course(self, course_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT course_id, course_name, credit, category, sub_category,
                   recommended_year, recommended_semester, is_offered, language, note
            FROM courses
            WHERE course_id = ?
            """,
            (course_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown course_id: {course_id}")
        return dict(row)

    def _offered_courses(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.conn.execute(
                """
                SELECT course_id, course_name, credit, category, sub_category,
                       recommended_year, recommended_semester, is_offered,
                       language, note
                FROM courses
                WHERE is_offered = 1
                ORDER BY course_id
                """
            ).fetchall()
        ]

    def _incoming_edges(
        self,
        course_id: str,
        relation_type: str,
    ) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.conn.execute(
                """
                SELECT from_course_id, to_course_id, relation_type, weight, reason
                FROM prerequisites
                WHERE to_course_id = ?
                  AND relation_type = ?
                ORDER BY weight DESC, from_course_id
                """,
                (course_id, relation_type),
            ).fetchall()
        ]

    def _completed_course_ids(self, student_id: str) -> set[str]:
        return {
            course["course_id"]
            for course in self.requirements.get_completed_courses(student_id)
        }

    @staticmethod
    def _matches_track(course: dict[str, Any], target_track: str | None) -> bool:
        if target_track == "PROFESSIONAL":
            return course["sub_category"] == "PROFESSIONAL_TRACK"
        if target_track == "TEACHER":
            return course["sub_category"] in {
                "TEACHER_TRACK",
                "SUBJECT_EDUCATION",
                "TEACHING_THEORY",
                "TEACHING_FOUNDATION",
                "TEACHING_PRACTICUM",
            }
        if target_track == "COMMON":
            return course["sub_category"] in {
                "BASIC_REQUIRED",
                "BASIC_REQUIRED_CHOICE",
                "MAJOR_COMMON",
                "TEACHING_THEORY",
            }
        return False


def _parse_numbers(value: str | None) -> set[int]:
    if not value:
        return set()
    numbers: set[int] = set()
    for token in value.replace(" ", "").split(","):
        if not token:
            continue
        if "-" in token:
            start, end = token.split("-", 1)
            if start.isdigit() and end.isdigit():
                numbers.update(range(int(start), int(end) + 1))
        elif token.isdigit():
            numbers.add(int(token))
    return numbers
