from __future__ import annotations

import unittest

from curriculum.db import initialize_memory_database
from curriculum.graph import has_cycle, load_graph, topological_sort
from curriculum.recommender import CurriculumRecommender
from curriculum.requirements import RequirementChecker


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
        self.assertTrue(all(not status["satisfied"] for status in statuses))

    def test_requirement_summary_returns_missing_items_for_s001(self) -> None:
        summary = self.checker.get_requirement_summary("S001")
        missing_ids = {
            item["requirement_id"]
            for item in self.checker.get_missing_requirements("S001")
        }
        self.assertEqual(summary["student"]["student_id"], "S001")
        self.assertIn("BASIC_REQUIRED", missing_ids)
        self.assertIn("SUBJECT_EDUCATION", missing_ids)
        self.assertIn("TEACHING_APTITUDE_CHARACTER", missing_ids)


if __name__ == "__main__":
    unittest.main()
