import json
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


class CatalogAPITests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        write_catalog(self.root)
        self.client = APIClient()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_lists_releases_and_active_year(self):
        with override_settings(
            UWPATH_CATALOG_ROOT=str(self.root),
            UWPATH_ACTIVE_ACADEMIC_YEAR="2025-2026",
        ):
            response = self.client.get("/api/catalogs/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_academic_year"], "2025-2026")
        self.assertEqual(response.data["catalogs"][0]["quality"]["course_count"], 1)
        self.assertEqual(response.data["catalogs"][0]["build"]["scope"], "full_catalog")

    def test_serves_active_courses_with_cache_headers(self):
        with override_settings(
            UWPATH_CATALOG_ROOT=str(self.root),
            UWPATH_ACTIVE_ACADEMIC_YEAR="2025-2026",
        ):
            response = self.client.get("/api/catalogs/active/courses/")
            cached_response = self.client.get(
                "/api/catalogs/active/courses/",
                HTTP_IF_NONE_MATCH=response["ETag"],
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["academic_year"], "2025-2026")
        self.assertEqual(response.data["courses"][0]["course_code"], "CS 135")
        self.assertEqual(response["Cache-Control"], "public, max-age=300")
        self.assertEqual(cached_response.status_code, 304)
        self.assertEqual(cached_response["ETag"], response["ETag"])

    def test_returns_not_found_for_an_unknown_year(self):
        with override_settings(UWPATH_CATALOG_ROOT=str(self.root)):
            response = self.client.get("/api/catalogs/2024-2025/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "catalog_not_found")

    def test_returns_unavailable_for_a_corrupt_release(self):
        courses_path = self.root / "2025-2026" / "courses.json"
        courses_path.write_text(json.dumps([]))

        with override_settings(UWPATH_CATALOG_ROOT=str(self.root)):
            response = self.client.get("/api/catalogs/2025-2026/courses/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"]["code"], "catalog_unavailable")

    def test_returns_unavailable_when_not_configured(self):
        with override_settings(UWPATH_CATALOG_ROOT=None):
            response = self.client.get("/api/catalogs/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"]["code"], "catalog_unavailable")
