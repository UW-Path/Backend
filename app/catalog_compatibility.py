"""Translate versioned catalog artifacts into the legacy planner API shapes."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from typing import Any

from app.catalog_repository import CatalogRepository, CatalogSnapshot

MATH_SUBJECTS = frozenset(
    {"ACTSC", "AMATH", "CO", "CS", "MATH", "MATBUS", "PMATH", "STAT"}
)
SCIENCE_SUBJECTS = frozenset({"BIOL", "CHEM", "EARTH", "PHYS", "SCI"})
LANGUAGE_SUBJECTS = frozenset(
    {
        "ARABIC",
        "CHINA",
        "CROAT",
        "DUTCH",
        "FR",
        "GER",
        "GRK",
        "ITAL",
        "JAPAN",
        "KOREA",
        "LAT",
        "PORT",
        "RUSS",
        "SPAN",
    }
)


class ProgramNotFound(Exception):
    """Raised when a legacy planner request names an unavailable program."""


def load_snapshot(
    repository: CatalogRepository,
    requested_year: str,
    preferred_year: str | None = None,
) -> CatalogSnapshot:
    year = repository.resolve_year(requested_year or "active", preferred_year)
    return repository.load(year)


def program_summary(program: Mapping[str, Any], academic_year: str) -> dict[str, Any]:
    title = str(program.get("title") or program.get("code") or "")
    return {
        "major_name": str(program.get("field_of_study") or title),
        "program_name": title,
        "plan_type": str(program.get("credential_type") or ""),
        "link": str(program.get("source_url") or ""),
        "year": academic_year,
    }


def major_summaries(snapshot: CatalogSnapshot) -> list[dict[str, Any]]:
    return _program_summaries(snapshot, {"Major"})


def available_program_years(
    repository: CatalogRepository, program_name: str
) -> list[dict[str, str]]:
    years = []
    for year in repository.available_years():
        snapshot = repository.load(year)
        if _find_program(snapshot, program_name, required=False) is not None:
            years.append({"year": year})
    return years


def requirements_payload(
    snapshot: CatalogSnapshot,
    major_name: str,
    minors: Iterable[str] = (),
    option: str = "",
) -> dict[str, Any]:
    major = _find_program(snapshot, major_name)
    requirements, warnings = _requirements_for_program(major, snapshot.academic_year)
    payload = {
        "major": major_name,
        "requirements": requirements,
        "minor_list": _program_summaries(snapshot, {"Minor"}),
        "option_list": _program_summaries(snapshot, {"Option", "Specialization"}),
        "table1": [],
        "table2": [],
        "compatibility_warnings": warnings,
    }

    selected_minors = [name for name in minors if name]
    if selected_minors:
        minor_requirements = {}
        for name in selected_minors:
            program = _find_program(snapshot, name)
            rows, program_warnings = _requirements_for_program(
                program, snapshot.academic_year
            )
            minor_requirements[name] = rows
            payload["compatibility_warnings"].extend(program_warnings)
        payload["minor"] = selected_minors
        payload["minor_requirements"] = minor_requirements

    if option:
        program = _find_program(snapshot, option)
        rows, program_warnings = _requirements_for_program(
            program, snapshot.academic_year
        )
        payload["option"] = option
        payload["option_requirements"] = rows
        payload["compatibility_warnings"].extend(program_warnings)

    return payload


def legacy_course(course: Mapping[str, Any]) -> dict[str, Any]:
    course_code = str(course.get("course_code") or "")
    subject = str(course.get("subject") or course_code.partition(" ")[0])
    number = str(course.get("number") or course_code.partition(" ")[2])
    numeric_match = re.match(r"\d+", number)
    return {
        "course_code": course_code,
        "course_abbr": subject,
        "course_number": int(numeric_match.group()) if numeric_match else 0,
        "course_id": _stable_course_id(course_code),
        "course_name": str(course.get("title") or ""),
        "credit": str(course.get("units") or "0.50"),
        "info": str(course.get("description") or ""),
        "offering": "",
        "is_online": False,
        "online": False,
        "prereqs": ",".join(_course_codes(course.get("prerequisite_rule"))),
        "coreqs": ",".join(_course_codes(course.get("corequisite_rule"))),
        "antireqs": ",".join(_course_codes(course.get("antirequisite_rule"))),
        "link": str(course.get("source_url") or ""),
    }


def find_course(snapshot: CatalogSnapshot, course_code: str) -> dict[str, Any]:
    normalized_code = _normalize_course_code(course_code)
    for course in snapshot.courses:
        if (
            _normalize_course_code(str(course.get("course_code") or ""))
            == normalized_code
        ):
            return legacy_course(course)
    raise ProgramNotFound(f"Course {course_code} is not available")


def filter_courses(
    snapshot: CatalogSnapshot, start: int, end: int, code: str
) -> list[dict[str, Any]]:
    courses = [legacy_course(course) for course in snapshot.courses]
    courses = [course for course in courses if start <= course["course_number"] <= end]

    code = code.strip()
    if code == "MATH":
        courses = _with_subjects(courses, MATH_SUBJECTS)
    elif code == "SCIENCE":
        courses = _with_subjects(courses, SCIENCE_SUBJECTS)
    elif code == "LANGUAGE":
        courses = _with_subjects(courses, LANGUAGE_SUBJECTS)
    elif code == "NON-MATH":
        courses = [
            course for course in courses if course["course_abbr"] not in MATH_SUBJECTS
        ]
    elif "LAB" in code:
        subject = code.partition(" ")[0]
        courses = [
            course
            for course in courses
            if course["course_abbr"] == subject
            and str(course["course_code"]).endswith("L")
        ]
    elif code.startswith("~") and any(character.isdigit() for character in code):
        excluded = {_normalize_course_code(value) for value in code[1:].split(",")}
        courses = [
            course
            for course in courses
            if _normalize_course_code(course["course_code"]) not in excluded
        ]
    elif code.startswith("~"):
        excluded = {value.strip() for value in code[1:].split(",")}
        courses = [
            course for course in courses if course["course_abbr"] not in excluded
        ]
    elif any(character.isdigit() for character in code):
        included = {_normalize_course_code(value) for value in code.split(",")}
        courses = [
            course
            for course in courses
            if _normalize_course_code(course["course_code"]) in included
        ]
    elif "," in code:
        courses = _with_subjects(courses, {value.strip() for value in code.split(",")})
    elif code != "none":
        courses = _with_subjects(courses, {code})

    return sorted(courses, key=lambda course: course["course_code"])


def _program_summaries(
    snapshot: CatalogSnapshot, credential_types: set[str]
) -> list[dict[str, Any]]:
    programs = (
        program
        for program in snapshot.programs
        if program.get("credential_type") in credential_types
    )
    return sorted(
        (program_summary(program, snapshot.academic_year) for program in programs),
        key=lambda program: program["program_name"],
    )


def _find_program(
    snapshot: CatalogSnapshot, name: str, required: bool = True
) -> Mapping[str, Any] | None:
    for program in snapshot.programs:
        if name in {program.get("title"), program.get("code")}:
            return program
    if required:
        raise ProgramNotFound(f"Program {name} is not available")
    return None


def _requirements_for_program(
    program: Mapping[str, Any], academic_year: str
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    _flatten_requirement_rule(program.get("requirement_rule"), rows, warnings, "root")
    summary = program_summary(program, academic_year)
    for index, row in enumerate(rows, start=1):
        row.update(
            {
                "id": index,
                "major_name": summary["major_name"],
                "program_name": summary["program_name"],
                "plan_type": summary["plan_type"],
                "year": academic_year,
                "faculty": str(program.get("faculty") or ""),
            }
        )
    for warning in warnings:
        warning["program_name"] = summary["program_name"]
    return rows, warnings


def _flatten_requirement_rule(
    rule: Any,
    rows: list[dict[str, Any]],
    warnings: list[dict[str, str]],
    path: str,
) -> None:
    if not isinstance(rule, Mapping):
        warnings.append(
            {
                "path": path,
                "type": "missing",
                "reason": "No structured requirement rule is available",
            }
        )
        return

    rule_type = rule.get("type")
    if rule_type == "course" and rule.get("course_code"):
        rows.append(_requirement_row([str(rule["course_code"])], 1))
        return

    children = rule.get("children")
    if rule_type == "all" and isinstance(children, list):
        for index, child in enumerate(children):
            _flatten_requirement_rule(child, rows, warnings, f"{path}.{index}")
        return

    if rule_type == "at_least" and isinstance(children, list):
        course_codes = [
            str(child.get("course_code"))
            for child in children
            if isinstance(child, Mapping)
            and child.get("type") == "course"
            and child.get("course_code")
        ]
        count = rule.get("count")
        if len(course_codes) == len(children) and isinstance(count, int) and count > 0:
            rows.append(_requirement_row(course_codes, count))
            return

    warnings.append(
        {
            "path": path,
            "type": str(rule_type or "unknown"),
            "reason": "Rule cannot be represented safely by the legacy planner",
            "source_text": str(rule.get("source_text") or ""),
        }
    )


def _requirement_row(course_codes: list[str], count: int) -> dict[str, Any]:
    return {
        "course_codes": ", ".join(course_codes),
        "number_of_courses": count,
        "credits_required": count * 0.5,
        "additional_requirements": "",
    }


def _course_codes(rule: Any) -> list[str]:
    if not isinstance(rule, Mapping):
        return []
    course_code = rule.get("course_code")
    if course_code:
        return [str(course_code)]
    children = rule.get("children")
    if not isinstance(children, list):
        return []
    return [code for child in children for code in _course_codes(child)]


def _stable_course_id(course_code: str) -> int:
    digest = hashlib.sha256(course_code.encode()).hexdigest()
    return int(digest[:12], 16)


def _normalize_course_code(course_code: str) -> str:
    return re.sub(r"\s+", "", course_code).upper()


def _with_subjects(
    courses: list[dict[str, Any]], subjects: Iterable[str]
) -> list[dict[str, Any]]:
    subjects = set(subjects)
    return [course for course in courses if course["course_abbr"] in subjects]
