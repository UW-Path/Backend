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


def course(code, title, units="0.50"):
    subject, number = code.split(" ", 1)
    return {
        "course_code": code,
        "subject": subject,
        "number": number,
        "title": title,
        "units": units,
        "description": f"Description for {code}",
        "source_url": f"https://example.test/courses/{subject}{number}",
        "prerequisite_rule": None,
        "corequisite_rule": None,
        "antirequisite_rule": None,
    }


def program(title, credential_type, rule, code="H-CS"):
    return {
        "code": code,
        "title": title,
        "credential_type": credential_type,
        "field_of_study": "Computer Science",
        "faculty": "Mathematics",
        "source_url": "https://example.test/programs/cs",
        "requirement_rule": rule,
    }


class CatalogCompatibilityAPITests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.courses = [
            course("CS 135", "Designing Functional Programs"),
            course("CS 136L", "Tools and Techniques", "0.25"),
            course("MATH 137", "Calculus 1"),
            course("HIST 101", "History"),
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
            ["CS 135", "CS 136L", "MATH 137"],
        )
        self.assertEqual([item["course_code"] for item in labs.json()], ["CS 136L"])
        self.assertEqual(
            [item["course_code"] for item in non_math.json()], ["HIST 101"]
        )

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
