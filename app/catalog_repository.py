"""Read immutable catalog releases produced by the DataParsing pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

SUPPORTED_SCHEMA_VERSION = 1
ACADEMIC_YEAR_PATTERN = re.compile(r"^\d{4}-\d{4}$")
REQUIRED_FILES = ("catalog.json", "courses.json", "programs.json")


class CatalogError(Exception):
    """Base class for catalog repository failures."""


class CatalogNotFound(CatalogError):
    """Raised when a requested academic year is unavailable."""


class CatalogIntegrityError(CatalogError):
    """Raised when a catalog release fails its integrity contract."""


@dataclass(frozen=True)
class CatalogSnapshot:
    academic_year: str
    manifest: Mapping[str, Any]
    courses: tuple[Mapping[str, Any], ...]
    programs: tuple[Mapping[str, Any], ...]
    etag: str

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "academic_year": self.academic_year,
            "schema_version": self.manifest["schema_version"],
            "source": self.manifest.get("source"),
            "source_id": self.manifest.get("source_id"),
            "generated_at": self.manifest.get("generated_at"),
            "build": self.manifest.get("build"),
            "quality": self.manifest["quality"],
            "etag": self.etag,
        }


class CatalogRepository:
    """Load and cache versioned catalog directories after verifying their manifest."""

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self._cache: dict[str, tuple[tuple[int, int, int], CatalogSnapshot]] = {}
        self._lock = RLock()

    def available_years(self) -> list[str]:
        if not self.root.is_dir():
            raise CatalogIntegrityError("Configured catalog root is not a directory")

        try:
            return sorted(
                entry.name
                for entry in self.root.iterdir()
                if entry.is_dir()
                and ACADEMIC_YEAR_PATTERN.fullmatch(entry.name)
                and (entry / "manifest.json").is_file()
            )
        except OSError as exc:
            raise CatalogIntegrityError("Unable to list catalog releases") from exc

    def resolve_year(
        self, requested_year: str, preferred_year: str | None = None
    ) -> str:
        if requested_year != "active":
            self._validate_year(requested_year)
            if requested_year not in self.available_years():
                raise CatalogNotFound(f"Catalog {requested_year} is not available")
            return requested_year

        if preferred_year:
            if not ACADEMIC_YEAR_PATTERN.fullmatch(preferred_year):
                raise CatalogIntegrityError(
                    "Configured active academic year is invalid"
                )
            if preferred_year not in self.available_years():
                raise CatalogIntegrityError(
                    f"Configured active catalog {preferred_year} is not available"
                )
            return preferred_year

        years = self.available_years()
        if not years:
            raise CatalogNotFound("No catalog releases are available")
        return years[-1]

    def load(self, academic_year: str) -> CatalogSnapshot:
        self._validate_year(academic_year)
        manifest_path = self.root / academic_year / "manifest.json"
        try:
            stat = manifest_path.stat()
        except FileNotFoundError as exc:
            raise CatalogNotFound(f"Catalog {academic_year} is not available") from exc
        except OSError as exc:
            raise CatalogIntegrityError("Unable to inspect catalog manifest") from exc

        cache_key = (stat.st_ino, stat.st_mtime_ns, stat.st_size)
        with self._lock:
            cached = self._cache.get(academic_year)
            if cached and cached[0] == cache_key:
                return cached[1]

            snapshot = self._load_uncached(academic_year, manifest_path)
            self._cache[academic_year] = (cache_key, snapshot)
            return snapshot

    @staticmethod
    def _validate_year(academic_year: str) -> None:
        if not ACADEMIC_YEAR_PATTERN.fullmatch(academic_year):
            raise CatalogNotFound("Invalid academic year")

    def _load_uncached(
        self, academic_year: str, manifest_path: Path
    ) -> CatalogSnapshot:
        manifest_bytes = self._read_bytes(manifest_path, "manifest.json")
        manifest = self._decode_object(manifest_bytes, "manifest.json")

        if manifest.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
            raise CatalogIntegrityError(
                "Catalog {} uses unsupported schema version {!r}".format(
                    academic_year, manifest.get("schema_version")
                )
            )
        if manifest.get("academic_year") != academic_year:
            raise CatalogIntegrityError(
                "Catalog directory and manifest academic year do not match"
            )

        files = manifest.get("files")
        if not isinstance(files, dict):
            raise CatalogIntegrityError("Manifest files must be an object")

        decoded: dict[str, list[Mapping[str, Any]]] = {}
        catalog: dict[str, Any] | None = None
        release_dir = manifest_path.parent
        for filename in REQUIRED_FILES:
            file_metadata = files.get(filename)
            if not isinstance(file_metadata, dict):
                raise CatalogIntegrityError(
                    f"Manifest is missing metadata for {filename}"
                )

            file_bytes = self._read_bytes(release_dir / filename, filename)
            self._verify_file(filename, file_bytes, file_metadata)
            if filename == "catalog.json":
                catalog = self._decode_object(file_bytes, filename)
            else:
                decoded[filename] = self._decode_list(file_bytes, filename)

        quality = manifest.get("quality")
        if not isinstance(quality, dict):
            raise CatalogIntegrityError("Manifest quality must be an object")
        if quality.get("publishable") is not True:
            raise CatalogIntegrityError("Catalog is not marked publishable")
        self._verify_count(quality, "course_count", decoded["courses.json"])
        self._verify_count(quality, "program_count", decoded["programs.json"])
        if catalog is None:
            raise CatalogIntegrityError("Catalog document is missing")
        self._verify_catalog_projection(
            manifest,
            catalog,
            decoded["courses.json"],
            decoded["programs.json"],
        )

        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        return CatalogSnapshot(
            academic_year=academic_year,
            manifest=manifest,
            courses=tuple(decoded["courses.json"]),
            programs=tuple(decoded["programs.json"]),
            etag=f'"{manifest_digest}"',
        )

    @staticmethod
    def _read_bytes(path: Path, label: str) -> bytes:
        try:
            return path.read_bytes()
        except OSError as exc:
            raise CatalogIntegrityError(f"Unable to read {label}") from exc

    @staticmethod
    def _decode_object(content: bytes, label: str) -> dict[str, Any]:
        try:
            value = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CatalogIntegrityError(f"{label} is not valid JSON") from exc
        if not isinstance(value, dict):
            raise CatalogIntegrityError(f"{label} must contain an object")
        return value

    @staticmethod
    def _decode_list(content: bytes, label: str) -> list[Mapping[str, Any]]:
        try:
            value = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CatalogIntegrityError(f"{label} is not valid JSON") from exc
        if not isinstance(value, list) or not all(
            isinstance(item, dict) for item in value
        ):
            raise CatalogIntegrityError(f"{label} must contain a list of objects")
        return value

    @staticmethod
    def _verify_file(
        filename: str, content: bytes, metadata: Mapping[str, Any]
    ) -> None:
        if metadata.get("bytes") != len(content):
            raise CatalogIntegrityError(f"{filename} byte count does not match")
        digest = hashlib.sha256(content).hexdigest()
        if metadata.get("sha256") != digest:
            raise CatalogIntegrityError(f"{filename} checksum does not match")

    @staticmethod
    def _verify_count(
        quality: Mapping[str, Any], key: str, records: list[Mapping[str, Any]]
    ) -> None:
        if quality.get(key) != len(records):
            raise CatalogIntegrityError(f"Manifest {key} does not match")

    @staticmethod
    def _verify_catalog_projection(
        manifest: Mapping[str, Any],
        catalog: Mapping[str, Any],
        courses: list[Mapping[str, Any]],
        programs: list[Mapping[str, Any]],
    ) -> None:
        calendar = catalog.get("calendar")
        if not isinstance(calendar, dict):
            raise CatalogIntegrityError("Catalog calendar must be an object")
        expected_metadata = {
            "schema_version": catalog.get("schema_version"),
            "academic_year": calendar.get("academic_year"),
            "generated_at": catalog.get("generated_at"),
            "source": calendar.get("source"),
            "source_id": calendar.get("source_id"),
            "quality": catalog.get("quality"),
        }
        for field_name, expected in expected_metadata.items():
            if manifest.get(field_name) != expected:
                raise CatalogIntegrityError(
                    f"Catalog and manifest {field_name} do not match"
                )
        if catalog.get("courses") != courses:
            raise CatalogIntegrityError("courses.json is not the catalog projection")
        if catalog.get("programs") != programs:
            raise CatalogIntegrityError("programs.json is not the catalog projection")
