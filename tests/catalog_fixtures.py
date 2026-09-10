import hashlib
import json


def write_catalog(
    root,
    year="2025-2026",
    courses=None,
    programs=None,
    publishable=True,
):
    courses = courses if courses is not None else [{"course_code": "CS 135"}]
    programs = programs if programs is not None else [{"code": "H-CS"}]
    release_directory = root / year
    release_directory.mkdir()
    quality = {
        "course_count": len(courses),
        "program_count": len(programs),
        "publishable": publishable,
        "planner_ready": False,
    }
    catalog = {
        "schema_version": 1,
        "generated_at": "2026-09-10T00:00:00+00:00",
        "calendar": {
            "academic_year": year,
            "source": "kuali",
            "source_id": "test-source",
        },
        "courses": courses,
        "programs": programs,
        "quality": quality,
    }
    files = {}
    for filename, value in (
        ("catalog.json", catalog),
        ("courses.json", courses),
        ("programs.json", programs),
    ):
        content = (json.dumps(value) + "\n").encode()
        (release_directory / filename).write_bytes(content)
        files[filename] = {
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    manifest = {
        "academic_year": year,
        "schema_version": 1,
        "source": "kuali",
        "source_id": "test-source",
        "generated_at": "2026-09-10T00:00:00+00:00",
        "build": {
            "scope": "full_catalog",
            "program_selectors": [],
            "raw_snapshot": True,
        },
        "files": files,
        "quality": quality,
    }
    (release_directory / "manifest.json").write_text(json.dumps(manifest))
    return release_directory
