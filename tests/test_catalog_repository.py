import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from app.catalog_repository import (
    CatalogIntegrityError,
    CatalogNotFound,
    CatalogRepository,
)
from tests.catalog_fixtures import write_catalog


class CatalogRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_catalog(
        self,
        year="2025-2026",
        courses=None,
        programs=None,
        publishable=True,
    ):
        return write_catalog(self.root, year, courses, programs, publishable)

    def test_loads_a_valid_release(self):
        self.write_catalog()

        snapshot = CatalogRepository(self.root).load("2025-2026")

        self.assertEqual(snapshot.academic_year, "2025-2026")
        self.assertEqual(snapshot.courses[0]["course_code"], "CS 135")
        self.assertEqual(snapshot.programs[0]["code"], "H-CS")
        self.assertEqual(snapshot.metadata["build"]["scope"], "full_catalog")
        self.assertTrue(snapshot.etag.startswith('"'))

    def test_lists_only_catalog_directories(self):
        self.write_catalog("2024-2025")
        self.write_catalog("2025-2026")
        (self.root / "staging").mkdir()

        self.assertEqual(
            CatalogRepository(self.root).available_years(),
            ["2024-2025", "2025-2026"],
        )

    def test_rejects_a_missing_catalog_root(self):
        missing_root = self.root / "missing"

        with self.assertRaisesRegex(CatalogIntegrityError, "not a directory"):
            CatalogRepository(missing_root).available_years()

    def test_resolves_configured_or_latest_active_year(self):
        self.write_catalog("2024-2025")
        self.write_catalog("2025-2026")
        repository = CatalogRepository(self.root)

        self.assertEqual(repository.resolve_year("active"), "2025-2026")
        self.assertEqual(repository.resolve_year("active", "2024-2025"), "2024-2025")

    def test_rejects_a_missing_configured_active_year(self):
        self.write_catalog("2025-2026")

        with self.assertRaisesRegex(CatalogIntegrityError, "Configured active"):
            CatalogRepository(self.root).resolve_year("active", "2024-2025")

    def test_rejects_path_traversal(self):
        with self.assertRaises(CatalogNotFound):
            CatalogRepository(self.root).load("../2025-2026")

    def test_rejects_a_checksum_mismatch(self):
        release_directory = self.write_catalog()
        (release_directory / "courses.json").write_text("[]")

        with self.assertRaisesRegex(CatalogIntegrityError, "byte count"):
            CatalogRepository(self.root).load("2025-2026")

    def test_rejects_an_unpublishable_release(self):
        self.write_catalog(publishable=False)

        with self.assertRaisesRegex(CatalogIntegrityError, "not marked publishable"):
            CatalogRepository(self.root).load("2025-2026")

    def test_rejects_a_manifest_count_mismatch(self):
        release_directory = self.write_catalog()
        manifest_path = release_directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["quality"]["course_count"] = 99
        manifest_path.write_text(json.dumps(manifest))

        with self.assertRaisesRegex(CatalogIntegrityError, "course_count"):
            CatalogRepository(self.root).load("2025-2026")

    def test_rejects_an_unsupported_schema(self):
        release_directory = self.write_catalog()
        manifest_path = release_directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schema_version"] = 2
        manifest_path.write_text(json.dumps(manifest))

        with self.assertRaisesRegex(CatalogIntegrityError, "unsupported schema"):
            CatalogRepository(self.root).load("2025-2026")

    def test_rejects_a_projection_that_disagrees_with_catalog(self):
        release_directory = self.write_catalog()
        catalog_path = release_directory / "catalog.json"
        manifest_path = release_directory / "manifest.json"
        catalog = json.loads(catalog_path.read_text())
        catalog["courses"] = []
        content = (json.dumps(catalog) + "\n").encode()
        catalog_path.write_bytes(content)
        manifest = json.loads(manifest_path.read_text())
        manifest["files"]["catalog.json"] = {
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        manifest_path.write_text(json.dumps(manifest))

        with self.assertRaisesRegex(CatalogIntegrityError, "catalog projection"):
            CatalogRepository(self.root).load("2025-2026")


if __name__ == "__main__":
    unittest.main()
