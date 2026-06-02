from __future__ import annotations

import sqlite3
from typing import Any


PASSING_FAIL_GRADES = {"F", "FAIL", "NP"}


class RequirementChecker:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get_completed_courses(self, student_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT c.course_id, c.course_name, c.credit, c.category, c.sub_category,
                   c.recommended_year, c.recommended_semester, c.is_offered,
                   cc.completed_year, cc.completed_semester, cc.grade, cc.score
            FROM completed_courses cc
            JOIN courses c ON c.course_id = cc.course_id
            WHERE cc.student_id = ?
            ORDER BY cc.completed_year, cc.completed_semester, c.course_id
            """,
            (student_id,),
        ).fetchall()
        return [dict(row) for row in rows if self._is_passing(row)]

    def calculate_completed_credits(
        self,
        student_id: str,
        category: str | None = None,
        sub_category: str | None = None,
    ) -> int:
        courses = self.get_completed_courses(student_id)
        return sum(
            course["credit"]
            for course in courses
            if (category is None or course["category"] == category)
            and (sub_category is None or course["sub_category"] == sub_category)
        )

    def check_major_total_credits(self, student_id: str) -> dict[str, Any]:
        return self._credit_requirement_status(
            student_id,
            requirement_id="MAJOR_CREDITS",
            category="MAJOR",
        )

    def check_basic_required_courses(self, student_id: str) -> dict[str, Any]:
        status = self._course_requirement_status(student_id, "BASIC_REQUIRED")
        status["choice_groups"] = [
            group
            for group in self.check_choice_groups(student_id)
            if group["requirement_id"] == "BASIC_REQUIRED"
        ]
        status["satisfied"] = status["satisfied"] and all(
            group["satisfied"] for group in status["choice_groups"]
        )
        return status

    def check_subject_education_area(self, student_id: str) -> dict[str, Any]:
        return self._course_requirement_status(student_id, "SUBJECT_EDUCATION")

    def check_teaching_total_credits(self, student_id: str) -> dict[str, Any]:
        return self._credit_requirement_status(
            student_id,
            requirement_id="TEACHING_CREDITS",
            category="TEACHING",
        )

    def check_teaching_theory(self, student_id: str) -> dict[str, Any]:
        return self._course_requirement_status(student_id, "TEACHING_THEORY")

    def check_teaching_foundation(self, student_id: str) -> dict[str, Any]:
        return self._course_requirement_status(student_id, "TEACHING_FOUNDATION")

    def check_teaching_practicum(self, student_id: str) -> dict[str, Any]:
        return self._course_requirement_status(student_id, "TEACHING_PRACTICUM")

    def check_choice_groups(self, student_id: str) -> list[dict[str, Any]]:
        completed_ids = self._completed_course_ids(student_id)
        groups = self.conn.execute(
            """
            SELECT choice_group_id, requirement_id, group_name,
                   required_select_count, description
            FROM choice_groups
            ORDER BY requirement_id, choice_group_id
            """
        ).fetchall()

        results: list[dict[str, Any]] = []
        for group in groups:
            courses = self.conn.execute(
                """
                SELECT c.course_id, c.course_name, c.credit
                FROM choice_group_courses cgc
                JOIN courses c ON c.course_id = cgc.course_id
                WHERE cgc.choice_group_id = ?
                ORDER BY c.course_id
                """,
                (group["choice_group_id"],),
            ).fetchall()
            options = [dict(course) for course in courses]
            completed = [
                course for course in options if course["course_id"] in completed_ids
            ]
            missing = [
                course for course in options if course["course_id"] not in completed_ids
            ]
            required_count = group["required_select_count"]
            completed_count = len(completed)
            results.append(
                {
                    "choice_group_id": group["choice_group_id"],
                    "requirement_id": group["requirement_id"],
                    "group_name": group["group_name"],
                    "required_select_count": required_count,
                    "completed_select_count": completed_count,
                    "satisfied": completed_count >= required_count,
                    "completed_courses": completed,
                    "missing_options": missing,
                    "description": group["description"],
                }
            )
        return results

    def check_non_course_requirements(self, student_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT n.requirement_id, n.requirement_name, n.required_count,
                   n.recommended_timing, n.description,
                   COALESCE(r.completed_count, 0) AS completed_count
            FROM non_course_requirements n
            LEFT JOIN student_non_course_records r
              ON r.requirement_id = n.requirement_id
             AND r.student_id = ?
            ORDER BY n.requirement_id
            """,
            (student_id,),
        ).fetchall()
        return [
            {
                "requirement_id": row["requirement_id"],
                "requirement_name": row["requirement_name"],
                "required_count": row["required_count"],
                "completed_count": row["completed_count"],
                "recommended_timing": row["recommended_timing"],
                "description": row["description"],
                "satisfied": row["completed_count"] >= row["required_count"],
                "missing_count": max(row["required_count"] - row["completed_count"], 0),
            }
            for row in rows
        ]

    def get_missing_requirements(self, student_id: str) -> list[dict[str, Any]]:
        summary = self.get_requirement_summary(student_id)
        missing = [
            requirement
            for requirement in summary["course_requirements"]
            if not requirement["satisfied"]
        ]
        missing.extend(
            requirement
            for requirement in summary["non_course_requirements"]
            if not requirement["satisfied"]
        )
        return missing

    def get_requirement_summary(self, student_id: str) -> dict[str, Any]:
        student = self.conn.execute(
            """
            SELECT student_id, student_name, current_year, current_semester, target_track
            FROM students
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchone()
        if student is None:
            raise ValueError(f"Unknown student_id: {student_id}")

        course_requirements = [
            self.check_major_total_credits(student_id),
            self.check_basic_required_courses(student_id),
            self.check_subject_education_area(student_id),
            self.check_teaching_total_credits(student_id),
            self.check_teaching_theory(student_id),
            self.check_teaching_foundation(student_id),
            self.check_teaching_practicum(student_id),
        ]
        non_course_requirements = self.check_non_course_requirements(student_id)
        return {
            "student": dict(student),
            "completed_courses": self.get_completed_courses(student_id),
            "course_requirements": course_requirements,
            "non_course_requirements": non_course_requirements,
            "course_requirements_satisfied": all(
                requirement["satisfied"] for requirement in course_requirements
            ),
            "non_course_requirements_satisfied": all(
                requirement["satisfied"] for requirement in non_course_requirements
            ),
        }

    def unmet_requirement_course_ids(self, student_id: str) -> dict[str, list[str]]:
        """Return course IDs that can help with each currently unmet requirement."""
        result: dict[str, list[str]] = {}
        for requirement in self.get_requirement_summary(student_id)["course_requirements"]:
            if requirement["satisfied"]:
                continue
            course_ids = {course["course_id"] for course in requirement["missing_courses"]}
            for group in requirement.get("choice_groups", []):
                if not group["satisfied"]:
                    course_ids.update(
                        course["course_id"] for course in group["missing_options"]
                    )
            for course in requirement.get("candidate_courses", []):
                if course["course_id"] not in self._completed_course_ids(student_id):
                    course_ids.add(course["course_id"])
            result[requirement["requirement_id"]] = sorted(course_ids)
        return result

    def requirement_relevance_for_course(
        self,
        student_id: str,
        course_id: str,
    ) -> list[str]:
        relevance: list[str] = []
        unmet = self.unmet_requirement_course_ids(student_id)
        names = self._requirement_names()
        for requirement_id, course_ids in unmet.items():
            if course_id in course_ids:
                relevance.append(names.get(requirement_id, requirement_id))
        return relevance

    def _credit_requirement_status(
        self,
        student_id: str,
        requirement_id: str,
        category: str,
    ) -> dict[str, Any]:
        requirement = self._requirement(requirement_id)
        completed_courses = [
            course
            for course in self.get_completed_courses(student_id)
            if course["category"] == category
        ]
        completed_credits = sum(course["credit"] for course in completed_courses)
        required_credits = requirement["required_credits"]
        return {
            "requirement_id": requirement_id,
            "requirement_name": requirement["requirement_name"],
            "category": requirement["category"],
            "required_credits": required_credits,
            "completed_credits": completed_credits,
            "required_course_count": requirement["required_course_count"],
            "completed_course_count": len(completed_courses),
            "satisfied": completed_credits >= required_credits,
            "missing_credits": max(required_credits - completed_credits, 0),
            "missing_courses": [],
            "candidate_courses": [],
            "choice_groups": [],
            "description": requirement["description"],
        }

    def _course_requirement_status(
        self,
        student_id: str,
        requirement_id: str,
    ) -> dict[str, Any]:
        requirement = self._requirement(requirement_id)
        completed_ids = self._completed_course_ids(student_id)
        courses = self._requirement_courses(requirement_id)
        candidate_courses = [course for course, _ in courses]
        completed_courses = [
            course for course in candidate_courses if course["course_id"] in completed_ids
        ]
        missing_mandatory = [
            course
            for course, is_mandatory in courses
            if is_mandatory and course["course_id"] not in completed_ids
        ]
        completed_credits = sum(course["credit"] for course in completed_courses)
        completed_count = len(completed_courses)
        required_credits = requirement["required_credits"] or 0
        required_count = requirement["required_course_count"] or 0
        satisfied = (
            completed_credits >= required_credits
            and completed_count >= required_count
            and not missing_mandatory
        )
        return {
            "requirement_id": requirement_id,
            "requirement_name": requirement["requirement_name"],
            "category": requirement["category"],
            "required_credits": requirement["required_credits"],
            "completed_credits": completed_credits,
            "required_course_count": requirement["required_course_count"],
            "completed_course_count": completed_count,
            "satisfied": satisfied,
            "missing_credits": max(required_credits - completed_credits, 0),
            "missing_course_count": max(required_count - completed_count, 0),
            "missing_courses": missing_mandatory,
            "candidate_courses": candidate_courses,
            "choice_groups": [],
            "description": requirement["description"],
        }

    def _requirement(self, requirement_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT requirement_id, requirement_name, category, required_credits,
                   required_course_count, description
            FROM requirements
            WHERE requirement_id = ?
            """,
            (requirement_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown requirement_id: {requirement_id}")
        return dict(row)

    def _requirement_courses(
        self,
        requirement_id: str,
    ) -> list[tuple[dict[str, Any], bool]]:
        rows = self.conn.execute(
            """
            SELECT c.course_id, c.course_name, c.credit, c.category, c.sub_category,
                   rc.is_mandatory
            FROM requirement_courses rc
            JOIN courses c ON c.course_id = rc.course_id
            WHERE rc.requirement_id = ?
            ORDER BY c.course_id
            """,
            (requirement_id,),
        ).fetchall()
        return [
            (
                {
                    "course_id": row["course_id"],
                    "course_name": row["course_name"],
                    "credit": row["credit"],
                    "category": row["category"],
                    "sub_category": row["sub_category"],
                },
                bool(row["is_mandatory"]),
            )
            for row in rows
        ]

    def _completed_course_ids(self, student_id: str) -> set[str]:
        return {course["course_id"] for course in self.get_completed_courses(student_id)}

    def _requirement_names(self) -> dict[str, str]:
        return {
            row["requirement_id"]: row["requirement_name"]
            for row in self.conn.execute(
                "SELECT requirement_id, requirement_name FROM requirements"
            ).fetchall()
        }

    @staticmethod
    def _is_passing(row: sqlite3.Row) -> bool:
        grade = (row["grade"] or "").strip().upper()
        score = row["score"]
        if grade in PASSING_FAIL_GRADES:
            return False
        if score is not None and score < 60:
            return False
        return True
