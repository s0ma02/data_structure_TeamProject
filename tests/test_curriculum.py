from __future__ import annotations

import unittest

from curriculum.db import initialize_memory_database
from curriculum.graph import has_cycle, load_graph, topological_sort
from curriculum.recommender import CurriculumRecommender
from curriculum.requirements import RequirementChecker
from api.main import StudentUpdate, update_student


class CurriculumRecommendationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = initialize_memory_database()
        self.checker = RequirementChecker(self.conn)
        self.recommender = CurriculumRecommender(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def test_database_initialization_works(self) -> None:
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
            74,
        )
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM prerequisites").fetchone()[0],
            52,
        )

    def test_teaching_course_ids_are_real_cftd_ids(self) -> None:
        placeholder_patterns = [
            f"EDU_{name}_%" for name in ("THEORY", "FOUNDATION", "PRACTICUM")
        ]
        placeholders = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM courses
            WHERE course_id LIKE ?
               OR course_id LIKE ?
               OR course_id LIKE ?
            """,
            placeholder_patterns,
        ).fetchone()[0]
        self.assertEqual(placeholders, 0)

        teaching_course_count = self.conn.execute(
            "SELECT COUNT(*) FROM courses WHERE category = 'TEACHING'"
        ).fetchone()[0]
        self.assertEqual(teaching_course_count, 14)

        duplicate_teaching_names = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT course_name
                FROM courses
                WHERE category = 'TEACHING'
                GROUP BY course_name
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        self.assertEqual(duplicate_teaching_names, 0)

        teaching_ids = {
            row[0]
            for row in self.conn.execute(
                "SELECT course_id FROM courses WHERE category = 'TEACHING'"
            ).fetchall()
        }
        self.assertEqual(
            teaching_ids,
            {
                "CFTD094",
                "CFTD008",
                "CFTD009",
                "CFTD007",
                "CFTD103",
                "CFTD104",
                "CFTD005",
                "CFTD006",
                "CFTD093",
                "CFTD123",
                "CFTD122",
                "CFTD119",
                "CFTD010",
                "CFTD078",
            },
        )

        cftd094 = self.conn.execute(
            "SELECT recommended_semester FROM courses WHERE course_id = 'CFTD094'"
        ).fetchone()
        self.assertEqual(cftd094[0], "1,2")

    def test_teaching_prerequisite_edges_use_cftd_ids(self) -> None:
        edges = {
            (row["from_course_id"], row["to_course_id"]): (
                row["relation_type"],
                row["weight"],
            )
            for row in self.conn.execute(
                """
                SELECT from_course_id, to_course_id, relation_type, weight
                FROM prerequisites
                WHERE from_course_id LIKE 'CFTD%' OR to_course_id LIKE 'CFTD%'
                """
            ).fetchall()
        }
        self.assertEqual(edges[("CFTD094", "CFTD007")], ("RECOMMENDED", 2))
        self.assertEqual(edges[("CFTD094", "CFTD008")], ("RECOMMENDED", 2))
        self.assertEqual(edges[("CFTD007", "CFTD103")], ("RECOMMENDED", 2))
        self.assertEqual(edges[("CFTD103", "CFTD104")], ("RECOMMENDED", 2))
        self.assertEqual(edges[("CFTD103", "CFTD005")], ("RECOMMENDED", 2))
        self.assertEqual(edges[("CFTD119", "CFTD010")], ("RECOMMENDED", 3))
        self.assertEqual(edges[("CFTD122", "CFTD010")], ("RECOMMENDED", 3))
        self.assertEqual(edges[("CFTD010", "CFTD078")], ("RECOMMENDED", 2))

    def test_dag_is_valid(self) -> None:
        courses, prerequisites = load_graph(self.conn)
        self.assertFalse(has_cycle(courses, prerequisites))

    def test_topological_sort_returns_all_courses(self) -> None:
        courses, prerequisites = load_graph(self.conn)
        order = topological_sort(courses, prerequisites)
        self.assertEqual(len(order), len(courses))
        self.assertLess(order.index("COM2002"), order.index("COM2012"))

    def test_com3026_blocked_without_com2012(self) -> None:
        recommendations = self.recommender.recommend_next_courses("S001", limit=100)
        course_ids = {item["course_id"] for item in recommendations}
        self.assertNotIn("COM3026", course_ids)

    def test_com2012_recommended_after_com2002(self) -> None:
        recommendations = self.recommender.recommend_next_courses("S001", limit=10)
        course_ids = {item["course_id"] for item in recommendations}
        self.assertIn("COM2012", course_ids)

    def test_choice_group_algorithm_ai_is_checked(self) -> None:
        groups = self.checker.check_choice_groups("S001")
        basic_group = next(
            group
            for group in groups
            if group["choice_group_id"] == "BASIC_REQUIRED_ALGORITHM_AI"
        )
        self.assertFalse(basic_group["satisfied"])
        self.assertEqual(basic_group["required_select_count"], 1)
        self.assertEqual(
            {course["course_id"] for course in basic_group["missing_options"]},
            {"COM3022", "COM3026"},
        )

    def test_non_course_requirements_are_checked(self) -> None:
        statuses = self.checker.check_non_course_requirements("S001")
        self.assertEqual(len(statuses), 5)
        self.assertTrue(all(status["satisfied"] for status in statuses))
        self.assertTrue(
            all(status["completed_count"] >= status["required_count"] for status in statuses)
        )

    def test_non_course_completed_flag_satisfies_requirement(self) -> None:
        self.conn.execute(
            """
            UPDATE student_non_course_records
            SET completed = 1, completed_count = 0, note = '완료 확인'
            WHERE student_id = 'S001'
              AND requirement_id = 'TEACHING_APTITUDE_CHARACTER'
            """
        )
        self.conn.commit()

        statuses = {
            status["requirement_id"]: status
            for status in self.checker.check_non_course_requirements("S001")
        }
        self.assertTrue(statuses["TEACHING_APTITUDE_CHARACTER"]["satisfied"])
        self.assertTrue(statuses["TEACHING_APTITUDE_CHARACTER"]["completed"])
        self.assertEqual(statuses["TEACHING_APTITUDE_CHARACTER"]["note"], "완료 확인")

    def test_non_course_count_satisfies_requirement(self) -> None:
        self.conn.execute(
            """
            UPDATE student_non_course_records
            SET completed = 0, completed_count = 2
            WHERE student_id = 'S001'
              AND requirement_id = 'CPR_TRAINING'
            """
        )
        self.conn.commit()

        statuses = {
            status["requirement_id"]: status
            for status in self.checker.check_non_course_requirements("S001")
        }
        self.assertTrue(statuses["CPR_TRAINING"]["satisfied"])
        self.assertTrue(statuses["CPR_TRAINING"]["completed"])

    def test_non_course_lower_count_can_be_unsatisfied(self) -> None:
        self.conn.execute(
            """
            UPDATE student_non_course_records
            SET completed = 0, completed_count = 1
            WHERE student_id = 'S001'
              AND requirement_id = 'CPR_TRAINING'
            """
        )
        self.conn.commit()

        statuses = {
            status["requirement_id"]: status
            for status in self.checker.check_non_course_requirements("S001")
        }
        self.assertFalse(statuses["CPR_TRAINING"]["satisfied"])
        self.assertEqual(statuses["CPR_TRAINING"]["missing_count"], 1)

    def test_student_profile_can_be_updated(self) -> None:
        # Mirrors the web profile form before recommendation outputs are refreshed.
        updated = update_student(
            "S001",
            StudentUpdate(
                name="김재혁",
                current_year=2,
                current_semester=1,
                track="TEACHER",
            ),
            self.conn,
        )
        self.assertEqual(updated["student_name"], "김재혁")
        self.assertEqual(updated["current_year"], 2)
        self.assertEqual(updated["current_semester"], 1)
        self.assertEqual(updated["target_track"], "TEACHER")

    def test_requirement_summary_returns_missing_items_for_s001(self) -> None:
        summary = self.checker.get_requirement_summary("S001")
        missing_ids = {
            item["requirement_id"]
            for item in self.checker.get_missing_requirements("S001")
        }
        self.assertEqual(summary["student"]["student_id"], "S001")
        self.assertIn("BASIC_REQUIRED", missing_ids)
        self.assertIn("SUBJECT_EDUCATION", missing_ids)
        self.assertNotIn("TEACHING_APTITUDE_CHARACTER", missing_ids)


if __name__ == "__main__":
    unittest.main()
