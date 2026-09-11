import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uwpath_backend.test_settings")

import django

django.setup()

from django.test import override_settings
from rest_framework.test import APIClient

from tests.catalog_fixtures import write_catalog


MAJOR_TITLE = "Computer Science (Bachelor of Computer Science - Honours)"
CS_PROGRAM_ENROLLMENT = (
    "Enrolled in H-BBA & BCS Double Degree , H-Computer Science (BCS) , "
    "H-Computer Science (BMath) , JH-Computer Science (BCS) , "
    "JH-Computer Science (BMath) , H-Computing & Financial Management , "
    "H-Data Science (BCS) , H-Data Science (BMath) , or H-Software Engineering"
)


def course(
    code,
    title,
    units="0.50",
    prerequisite_rule=None,
    corequisite_rule=None,
    antirequisite_rule=None,
):
    subject, number = code.split(" ", 1)
    return {
        "course_code": code,
        "subject": subject,
        "number": number,
        "title": title,
        "units": units,
        "description": f"Description for {code}",
        "source_url": f"https://example.test/courses/{subject}{number}",
        "prerequisite_rule": prerequisite_rule,
        "corequisite_rule": corequisite_rule,
        "antirequisite_rule": antirequisite_rule,
    }


def program(
    title,
    credential_type,
    rule,
    code="H-Computer Science (BCS)",
    faculty="Faculty of Mathematics",
):
    return {
        "code": code,
        "title": title,
        "credential_type": credential_type,
        "field_of_study": "Computer Science",
        "faculty": faculty,
        "source_url": "https://example.test/programs/cs",
        "requirement_rule": rule,
    }


class CatalogCompatibilityAPITests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.courses = [
            course("CS 135", "Designing Functional Programs"),
            course(
                "CS 136",
                "Elementary Algorithm Design",
                prerequisite_rule={
                    "type": "at_least",
                    "count": 1,
                    "source_text": "Complete 1 of CS 135 or CS 145",
                    "children": [
                        {"type": "course", "course_code": "CS 135"},
                        {"type": "course", "course_code": "CS 145"},
                    ],
                },
                corequisite_rule={"type": "course", "course_code": "CS 136L"},
                antirequisite_rule={
                    "type": "none_of",
                    "children": [{"type": "course", "course_code": "CS 137"}],
                },
            ),
            course(
                "CS 136L",
                "Tools and Techniques",
                "0.25",
                prerequisite_rule={
                    "type": "at_least",
                    "count": 1,
                    "source_text": "Complete 1 prerequisite group",
                    "children": [
                        {
                            "type": "at_least",
                            "count": 1,
                            "source_text": "Earned a minimum grade in CS 135",
                            "children": [{"type": "course", "course_code": "CS 135"}],
                        }
                    ],
                },
                corequisite_rule={
                    "type": "at_least",
                    "count": 1,
                    "source_text": "Completed or concurrently enrolled",
                    "children": [
                        {"type": "course", "course_code": "CS 136"},
                        {"type": "course", "course_code": "CS 146"},
                    ],
                },
            ),
            course(
                "CS 241",
                "Foundations of Sequential Programs",
                prerequisite_rule={
                    "type": "manual",
                    "source_text": CS_PROGRAM_ENROLLMENT,
                },
            ),
            course(
                "MATH 135",
                "Algebra for Honours Mathematics",
                prerequisite_rule={
                    "type": "all",
                    "children": [
                        {
                            "type": "manual",
                            "source_text": (
                                "Must have completed at least 1 of the following: "
                                "4U Calculus and Vectors, 4U Mathematics of Data "
                                "Management"
                            ),
                        },
                        {
                            "type": "at_least",
                            "count": 1,
                            "children": [
                                {
                                    "type": "manual",
                                    "source_text": (
                                        "Enrolled in H-Mathematical Physics (BSc) , "
                                        "or H-Software Engineering"
                                    ),
                                },
                                {
                                    "type": "manual",
                                    "source_text": (
                                        "Enrolled in an Honours Mathematics program "
                                        "or Mathematics/BASE"
                                    ),
                                },
                            ],
                        },
                    ],
                },
                antirequisite_rule={
                    "type": "none_of",
                    "children": [{"type": "course", "course_code": "MATH 145"}],
                },
            ),
            course(
                "MATH 137",
                "Calculus 1",
                prerequisite_rule={
                    "type": "manual",
                    "source_text": (
                        "Must have completed the following: 4U Calculus and Vectors"
                    ),
                },
            ),
            course(
                "MATH 136",
                "Linear Algebra 1 for Honours Mathematics",
                prerequisite_rule={
                    "type": "all",
                    "children": [
                        {
                            "type": "at_least",
                            "count": 1,
                            "children": [
                                {"type": "course", "course_code": "MATH 135"},
                                {"type": "course", "course_code": "MATH 145"},
                            ],
                        },
                        {
                            "type": "at_least",
                            "count": 1,
                            "children": [
                                {
                                    "type": "manual",
                                    "source_text": "Enrolled in H-Mathematical Physics (BSc)",
                                },
                                {
                                    "type": "manual",
                                    "source_text": "Enrolled in an Honours Mathematics program or Mathematics/BASE",
                                },
                            ],
                        },
                    ],
                },
            ),
            course(
                "HIST 101",
                "History",
                prerequisite_rule={
                    "type": "manual",
                    "source_text": "Permission of the department",
                },
            ),
            course(
                "HIST 401",
                "Advanced History",
                prerequisite_rule={
                    "type": "manual",
                    "source_text": "Permission of the department",
                },
                corequisite_rule={"type": "course", "course_code": "CS 135"},
                antirequisite_rule={
                    "type": "manual",
                    "source_text": "Not open to exchange students",
                },
            ),
            course(
                "ACTSC 221",
                "Introductory Financial Mathematics",
                prerequisite_rule={
                    "type": "manual",
                    "source_text": "Students must be in level 2A or higher",
                },
                antirequisite_rule={
                    "type": "all",
                    "children": [
                        {
                            "type": "none_of",
                            "children": [
                                {"type": "course", "course_code": "ACTSC 231"}
                            ],
                        },
                        {
                            "type": "manual",
                            "source_text": (
                                "Not open to students enrolled in H-Actuarial "
                                "Science , or JH-Actuarial Science"
                            ),
                        },
                        {
                            "type": "all",
                            "children": [
                                {
                                    "type": "manual",
                                    "source_text": (
                                        "The following antirequisites are only for "
                                        "students in the Faculty of Mathematics."
                                    ),
                                },
                                {
                                    "type": "none_of",
                                    "children": [
                                        {
                                            "type": "course",
                                            "course_code": "CIVE 392",
                                        }
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ),
        ]
        self.programs = [
            program(
                MAJOR_TITLE,
                "Major",
                {
                    "type": "all",
                    "children": [
                        {"type": "course", "course_code": "CS 135"},
                        {
                            "type": "at_least",
                            "count": 1,
                            "children": [
                                {"type": "course", "course_code": "CS 136L"},
                                {"type": "course", "course_code": "MATH 137"},
                            ],
                        },
                        {
                            "type": "manual",
                            "source_text": "Complete a work term requirement",
                        },
                    ],
                },
            ),
            program(
                "Computing Minor",
                "Minor",
                {"type": "course", "course_code": "CS 135"},
                "M-COMPUTING",
            ),
            program(
                "Artificial Intelligence Option",
                "Option",
                {"type": "course", "course_code": "CS 136L"},
                "O-AI",
            ),
            program(
                "Actuarial Science",
                "Test",
                {"type": "course", "course_code": "ACTSC 221"},
                "H-Actuarial Science",
            ),
            program(
                "History",
                "Test",
                {"type": "course", "course_code": "HIST 101"},
                "H-History",
                "Faculty of Arts",
            ),
        ]
        write_catalog(
            self.root,
            year="2025-2026",
            courses=self.courses,
            programs=self.programs,
        )
        write_catalog(
            self.root,
            year="2026-2027",
            courses=self.courses,
            programs=self.programs,
        )
        self.client = APIClient()
        self.settings = override_settings(
            UWPATH_CATALOG_ROOT=str(self.root),
            UWPATH_ACTIVE_ACADEMIC_YEAR="2026-2027",
        )
        self.settings.enable()

    def tearDown(self):
        self.settings.disable()
        self.temporary_directory.cleanup()

    def test_lists_active_catalog_majors_in_legacy_shape(self):
        response = self.client.get("/api/requirements/unique_major/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["Major"],
            [
                {
                    "major_name": "Computer Science",
                    "program_name": MAJOR_TITLE,
                    "plan_type": "Major",
                    "link": "https://example.test/programs/cs",
                    "year": "2026-2027",
                }
            ],
        )

    def test_lists_every_catalog_year_containing_a_program(self):
        response = self.client.get(
            "/api/requirements/get_available_year_for_program/",
            {"major": MAJOR_TITLE},
        )

        self.assertEqual(
            response.json()["years"],
            [{"year": "2025-2026"}, {"year": "2026-2027"}],
        )

    def test_translates_only_requirements_the_legacy_planner_can_represent(self):
        response = self.client.get(
            "/api/requirements/requirements/",
            {
                "major": MAJOR_TITLE,
                "calendar_year": "2026-2027",
                "minors": "",
                "option": "",
            },
        )
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["course_codes"] for row in data["requirements"]],
            ["CS 135", "CS 136L, MATH 137"],
        )
        self.assertEqual(data["requirements"][1]["number_of_courses"], 1)
        self.assertEqual(data["minor_list"][0]["program_name"], "Computing Minor")
        self.assertEqual(
            data["option_list"][0]["program_name"],
            "Artificial Intelligence Option",
        )
        self.assertEqual(data["compatibility_warnings"][0]["type"], "manual")

    def test_serves_course_detail_and_legacy_filters(self):
        detail = self.client.get("/api/course-info/get/", {"pk": "CS 136L"})
        math = self.client.get(
            "/api/course-info/filter/", {"start": 100, "end": 199, "code": "MATH"}
        )
        labs = self.client.get(
            "/api/course-info/filter/", {"start": 100, "end": 199, "code": "CS LAB"}
        )
        non_math = self.client.get(
            "/api/course-info/filter/",
            {"start": 100, "end": 199, "code": "NON-MATH"},
        )

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["course_name"], "Tools and Techniques")
        self.assertEqual(detail.json()["credit"], "0.25")
        self.assertEqual(
            [item["course_code"] for item in math.json()],
            [
                "CS 135",
                "CS 136",
                "CS 136L",
                "MATH 135",
                "MATH 136",
                "MATH 137",
            ],
        )
        self.assertEqual([item["course_code"] for item in labs.json()], ["CS 136L"])
        self.assertEqual(
            [item["course_code"] for item in non_math.json()], ["HIST 101"]
        )

    def test_validates_prerequisites_and_same_term_corequisites(self):
        params = [
            ("list_of_courses_taken[]", "CS 135"),
            ("current_term_courses[]", "CS 136"),
            ("current_term_courses[]", "CS 136L"),
        ]
        cs_136 = self.client.get("/api/meets_prereqs/get/", [*params, ("pk", "CS 136")])
        cs_136l = self.client.get(
            "/api/meets_prereqs/get/", [*params, ("pk", "CS 136L")]
        )

        self.assertEqual(cs_136.status_code, 200)
        self.assertTrue(cs_136.json()["can_take"])
        self.assertTrue(cs_136l.json()["can_take"])
        self.assertEqual(cs_136l.json()["verification"], "structured_course_membership")

    def test_explains_failed_and_unverifiable_rules(self):
        missing_prerequisite = self.client.get(
            "/api/meets_prereqs/get/",
            [("current_term_courses[]", "CS 136L"), ("pk", "CS 136")],
        )
        antirequisite = self.client.get(
            "/api/meets_prereqs/get/",
            [
                ("list_of_courses_taken[]", "CS 135"),
                ("current_term_courses[]", "CS 136L"),
                ("current_term_courses[]", "CS 137"),
                ("pk", "CS 136"),
            ],
        )
        manual = self.client.get("/api/meets_prereqs/get/", {"pk": "HIST 101"})
        manual_with_failed_corequisite = self.client.get(
            "/api/meets_prereqs/get/", {"pk": "HIST 401"}
        )

        self.assertFalse(missing_prerequisite.json()["can_take"])
        self.assertIn("Prerequisite not met", missing_prerequisite.json()["msg"])
        self.assertFalse(antirequisite.json()["can_take"])
        self.assertIn("CS137", antirequisite.json()["msg"])
        self.assertTrue(manual.json()["can_take"])
        self.assertEqual(
            manual.json()["verification"], "manual_review_recommended"
        )
        self.assertIn(
            "Permission of the department", manual.json()["advisories"][0]
        )
        self.assertFalse(manual_with_failed_corequisite.json()["can_take"])
        self.assertIn(
            "Corequisite not met", manual_with_failed_corequisite.json()["msg"]
        )

    def test_validates_honours_mathematics_enrollment_from_selected_program(self):
        params = [
            ("list_of_courses_taken[]", "MATH 135"),
            ("current_term_courses[]", "MATH 136"),
            ("programs[]", MAJOR_TITLE),
            ("pk", "MATH 136"),
        ]

        response = self.client.get("/api/meets_prereqs/get/", params)
        without_program = self.client.get(
            "/api/meets_prereqs/get/",
            [
                ("list_of_courses_taken[]", "MATH 135"),
                ("current_term_courses[]", "MATH 136"),
                ("pk", "MATH 136"),
            ],
        )

        self.assertTrue(response.json()["can_take"])
        self.assertTrue(without_program.json()["can_take"])
        self.assertEqual(
            without_program.json()["verification"], "manual_review_recommended"
        )

    def test_assumes_secondary_school_prerequisites_are_satisfied(self):
        math_135 = self.client.get(
            "/api/meets_prereqs/get/",
            {"programs[]": MAJOR_TITLE, "pk": "MATH 135"},
        )
        math_137 = self.client.get(
            "/api/meets_prereqs/get/",
            {"programs[]": MAJOR_TITLE, "pk": "MATH 137"},
        )

        self.assertTrue(math_135.json()["can_take"])
        self.assertEqual(
            math_135.json()["verification"], "structured_course_membership"
        )
        self.assertTrue(math_137.json()["can_take"])
        self.assertEqual(
            math_137.json()["verification"], "structured_course_membership"
        )

    def test_validates_selected_program_from_enrollment_list(self):
        response = self.client.get(
            "/api/meets_prereqs/get/",
            [
                ("current_term_courses[]", "CS 241"),
                ("programs[]", MAJOR_TITLE),
                ("pk", "CS 241"),
            ],
        )
        ineligible = self.client.get(
            "/api/meets_prereqs/get/",
            [
                ("current_term_courses[]", "CS 241"),
                ("programs[]", "Computing Minor"),
                ("pk", "CS 241"),
            ],
        )

        self.assertTrue(response.json()["can_take"])
        self.assertEqual(
            response.json()["verification"], "structured_course_membership"
        )
        self.assertEqual(
            ineligible.json()["msg"],
            "Prerequisite not met: Selected program is not listed as eligible for "
            "this course",
        )

    def test_validates_level_and_program_scoped_antirequisites(self):
        eligible = self.client.get(
            "/api/meets_prereqs/get/",
            {
                "academic_level": "2A",
                "programs[]": MAJOR_TITLE,
                "pk": "ACTSC 221",
            },
        )
        too_early = self.client.get(
            "/api/meets_prereqs/get/",
            {
                "academic_level": "1B",
                "programs[]": MAJOR_TITLE,
                "pk": "ACTSC 221",
            },
        )
        unknown_level = self.client.get(
            "/api/meets_prereqs/get/",
            {"programs[]": MAJOR_TITLE, "pk": "ACTSC 221"},
        )
        blocked_program = self.client.get(
            "/api/meets_prereqs/get/",
            {
                "academic_level": "2A",
                "programs[]": "Actuarial Science",
                "pk": "ACTSC 221",
            },
        )
        scoped_out = self.client.get(
            "/api/meets_prereqs/get/",
            {
                "academic_level": "2A",
                "current_term_courses[]": "CIVE 392",
                "programs[]": "History",
                "pk": "ACTSC 221",
            },
        )
        scoped_in = self.client.get(
            "/api/meets_prereqs/get/",
            {
                "academic_level": "2A",
                "current_term_courses[]": "CIVE 392",
                "programs[]": MAJOR_TITLE,
                "pk": "ACTSC 221",
            },
        )

        self.assertTrue(eligible.json()["can_take"])
        self.assertEqual(
            eligible.json()["verification"], "structured_course_membership"
        )
        self.assertFalse(too_early.json()["can_take"])
        self.assertIn("Students must be in level 2A", too_early.json()["msg"])
        self.assertEqual(
            unknown_level.json()["verification"], "manual_review_recommended"
        )
        self.assertFalse(blocked_program.json()["can_take"])
        self.assertIn("H-Actuarial Science", blocked_program.json()["msg"])
        self.assertTrue(scoped_out.json()["can_take"])
        self.assertFalse(scoped_in.json()["can_take"])
        self.assertIn("CIVE392", scoped_in.json()["msg"])

    def test_returns_not_found_for_an_unknown_program(self):
        response = self.client.get(
            "/api/requirements/requirements/",
            {
                "major": "Unknown",
                "calendar_year": "2026-2027",
                "minors": "",
                "option": "",
            },
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
