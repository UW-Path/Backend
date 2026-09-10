"""Conservative prerequisite checks over structured catalog course rules."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.catalog_compatibility import find_catalog_course, find_catalog_program
from app.catalog_repository import CatalogSnapshot


class RuleStatus(Enum):
    SATISFIED = "satisfied"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RuleResult:
    status: RuleStatus
    detail: str = ""


def validate_course_selection(
    snapshot: CatalogSnapshot,
    course_code: str,
    completed_courses: list[str],
    current_term_courses: list[str],
    selected_program_names: list[str] | None = None,
    academic_level: str | None = None,
) -> dict[str, Any]:
    course = find_catalog_course(snapshot, course_code)
    selected_programs = [
        find_catalog_program(snapshot, name) for name in selected_program_names or []
    ]
    normalized_course = _normalize_course_code(course_code)
    completed = _course_aliases(completed_courses)
    current = _course_aliases(current_term_courses)
    advisories: list[str] = []

    if normalized_course in completed:
        return _failure("Course has already been taken.", "failed")

    antirequisite = _evaluate_antirequisite_rule(
        course.get("antirequisite_rule"), completed | current, selected_programs
    )
    if antirequisite.status is RuleStatus.FAILED:
        return _failure(
            f"The course has an antirequisite: {antirequisite.detail}", "failed"
        )
    if antirequisite.status is RuleStatus.UNKNOWN:
        advisories.append(_manual_advisory("antirequisite", antirequisite.detail))

    prerequisite = _evaluate_membership_rule(
        course.get("prerequisite_rule"),
        completed,
        selected_programs,
        academic_level,
        assume_secondary_school_prerequisites=True,
    )
    if prerequisite.status is RuleStatus.FAILED:
        return _failure(f"Prerequisite not met: {prerequisite.detail}", "failed")
    if prerequisite.status is RuleStatus.UNKNOWN:
        advisories.append(_manual_advisory("prerequisite", prerequisite.detail))

    corequisite = _evaluate_membership_rule(
        course.get("corequisite_rule"),
        completed | current,
        selected_programs,
        academic_level,
    )
    if corequisite.status is RuleStatus.FAILED:
        return _failure(f"Corequisite not met: {corequisite.detail}", "failed")
    if corequisite.status is RuleStatus.UNKNOWN:
        advisories.append(_manual_advisory("corequisite", corequisite.detail))

    if advisories:
        return {
            "can_take": True,
            "msg": "",
            "verification": "manual_review_recommended",
            "advisories": advisories,
        }

    return {
        "can_take": True,
        "msg": "",
        "verification": "structured_course_membership",
    }


def _evaluate_membership_rule(
    rule: Any,
    available: set[str],
    selected_programs: list[Mapping[str, Any]],
    academic_level: str | None,
    assume_secondary_school_prerequisites: bool = False,
) -> RuleResult:
    if rule is None:
        return RuleResult(RuleStatus.SATISFIED)
    if not isinstance(rule, Mapping):
        return RuleResult(RuleStatus.UNKNOWN, "Invalid catalog rule")

    rule_type = rule.get("type")
    detail = str(rule.get("source_text") or rule.get("course_code") or "")
    if rule_type == "course":
        course_code = _normalize_course_code(str(rule.get("course_code") or ""))
        status = RuleStatus.SATISFIED if course_code in available else RuleStatus.FAILED
        return RuleResult(status, detail)

    if rule_type == "manual":
        return _evaluate_manual_rule(
            detail,
            selected_programs,
            academic_level,
            assume_secondary_school_prerequisites,
        )

    children = rule.get("children")
    if not isinstance(children, list):
        return RuleResult(RuleStatus.UNKNOWN, detail or "Rule has no children")
    results = [
        _evaluate_membership_rule(
            child,
            available,
            selected_programs,
            academic_level,
            assume_secondary_school_prerequisites,
        )
        for child in children
    ]

    if rule_type == "all":
        failed = next(
            (result for result in results if result.status is RuleStatus.FAILED), None
        )
        if failed:
            return failed
        unknown = next(
            (result for result in results if result.status is RuleStatus.UNKNOWN), None
        )
        return unknown or RuleResult(RuleStatus.SATISFIED)

    if rule_type == "at_least":
        count = rule.get("count")
        if not isinstance(count, int) or count < 1:
            return RuleResult(RuleStatus.UNKNOWN, detail or "Invalid course count")
        satisfied = sum(result.status is RuleStatus.SATISFIED for result in results)
        unknown = sum(result.status is RuleStatus.UNKNOWN for result in results)
        if satisfied >= count:
            return RuleResult(RuleStatus.SATISFIED)
        if satisfied + unknown < count:
            return RuleResult(RuleStatus.FAILED, detail)
        unknown_detail = next(
            (
                result.detail
                for result in results
                if result.status is RuleStatus.UNKNOWN and result.detail
            ),
            detail,
        )
        return RuleResult(RuleStatus.UNKNOWN, unknown_detail)

    return RuleResult(RuleStatus.UNKNOWN, detail or f"Unsupported {rule_type} rule")


def _evaluate_manual_rule(
    text: str,
    selected_programs: list[Mapping[str, Any]],
    academic_level: str | None,
    assume_secondary_school_prerequisites: bool,
) -> RuleResult:
    if assume_secondary_school_prerequisites and _is_secondary_school_prerequisite(
        text
    ):
        return RuleResult(RuleStatus.SATISFIED)

    required_level = re.fullmatch(
        r"Students must be in level\s+(\d+)([AB])\s+or higher", text, re.IGNORECASE
    )
    if required_level:
        if not academic_level:
            return RuleResult(RuleStatus.UNKNOWN, text)
        current_level = re.fullmatch(r"(\d+)([AB])", academic_level, re.IGNORECASE)
        if not current_level:
            return RuleResult(RuleStatus.UNKNOWN, text)
        required_rank = int(required_level.group(1)) * 2 + (
            required_level.group(2).upper() == "B"
        )
        current_rank = int(current_level.group(1)) * 2 + (
            current_level.group(2).upper() == "B"
        )
        status = (
            RuleStatus.SATISFIED if current_rank >= required_rank else RuleStatus.FAILED
        )
        return RuleResult(status, text)

    return _evaluate_enrollment_rule(text, selected_programs)


def _is_secondary_school_prerequisite(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:4[UM]|(?:Ontario\s+)?Grade\s+1[12]|high[- ]school)\b",
            text,
            re.IGNORECASE,
        )
    )


def _evaluate_enrollment_rule(
    text: str, selected_programs: list[Mapping[str, Any]]
) -> RuleResult:
    if not selected_programs or not text.startswith("Enrolled in "):
        return RuleResult(RuleStatus.UNKNOWN, text)

    selector = text.removeprefix("Enrolled in ")
    eligible_program_codes = _enrollment_program_codes(selector)
    if eligible_program_codes:
        selected_program_codes = {
            str(program.get("code") or "") for program in selected_programs
        }
        status = (
            RuleStatus.SATISFIED
            if eligible_program_codes & selected_program_codes
            else RuleStatus.FAILED
        )
        detail = (
            text
            if status is RuleStatus.SATISFIED
            else "Selected program is not listed as eligible for this course"
        )
        return RuleResult(status, detail)

    if selector in {
        "an Honours Mathematics program",
        "an Honours Mathematics program or Mathematics/BASE",
    }:
        status = (
            RuleStatus.SATISFIED
            if any(
                _is_honours_mathematics_program(program)
                for program in selected_programs
            )
            else RuleStatus.FAILED
        )
        return RuleResult(status, text)

    return RuleResult(RuleStatus.UNKNOWN, text)


def _enrollment_program_codes(selector: str) -> set[str]:
    alternatives = re.split(r"\s*,\s*(?:or\s+)?|\s+or\s+", selector)
    return {
        alternative.strip()
        for alternative in alternatives
        if alternative.strip().startswith(("H-", "JH-"))
    }


def _is_honours_mathematics_program(program: Mapping[str, Any]) -> bool:
    code = str(program.get("code") or "")
    return (
        program.get("faculty") == "Faculty of Mathematics"
        and code.startswith(("H-", "JH-"))
    ) or "Mathematics/BASE" in code


def _evaluate_antirequisite_rule(
    rule: Any,
    enrolled: set[str],
    selected_programs: list[Mapping[str, Any]],
) -> RuleResult:
    if rule is None:
        return RuleResult(RuleStatus.SATISFIED)
    if not isinstance(rule, Mapping):
        return RuleResult(RuleStatus.UNKNOWN, "Invalid catalog rule")

    rule_type = rule.get("type")
    detail = str(rule.get("source_text") or rule.get("course_code") or "")
    if rule_type == "course":
        course_code = _normalize_course_code(str(rule.get("course_code") or ""))
        status = RuleStatus.FAILED if course_code in enrolled else RuleStatus.SATISFIED
        return RuleResult(status, course_code if status is RuleStatus.FAILED else "")

    if rule_type == "manual":
        return _evaluate_antirequisite_manual(detail, selected_programs)

    children = rule.get("children")
    if not isinstance(children, list):
        return RuleResult(RuleStatus.UNKNOWN, detail or "Rule has no children")

    scoped_faculty = next(
        (
            _faculty_scope(child)
            for child in children
            if _faculty_scope(child) is not None
        ),
        None,
    )
    if scoped_faculty:
        if not selected_programs:
            return RuleResult(RuleStatus.UNKNOWN, scoped_faculty[1])
        if not any(
            str(program.get("faculty") or "") == scoped_faculty[0]
            for program in selected_programs
        ):
            return RuleResult(RuleStatus.SATISFIED)
        children = [child for child in children if _faculty_scope(child) is None]

    results = [
        _evaluate_antirequisite_rule(child, enrolled, selected_programs)
        for child in children
    ]
    failed = next(
        (result for result in results if result.status is RuleStatus.FAILED), None
    )
    if failed:
        return failed
    unknown = next(
        (result for result in results if result.status is RuleStatus.UNKNOWN), None
    )
    return unknown or RuleResult(RuleStatus.SATISFIED)


def _evaluate_antirequisite_manual(
    text: str, selected_programs: list[Mapping[str, Any]]
) -> RuleResult:
    prefix = "Not open to students enrolled in "
    if text.startswith(prefix):
        enrollment = _evaluate_enrollment_rule(
            f"Enrolled in {text.removeprefix(prefix)}", selected_programs
        )
        if enrollment.status is RuleStatus.SATISFIED:
            return RuleResult(RuleStatus.FAILED, text)
        if enrollment.status is RuleStatus.FAILED:
            return RuleResult(RuleStatus.SATISFIED)
    return RuleResult(RuleStatus.UNKNOWN, text)


def _faculty_scope(rule: Any) -> tuple[str, str] | None:
    if not isinstance(rule, Mapping) or rule.get("type") != "manual":
        return None
    text = str(rule.get("source_text") or "")
    match = re.fullmatch(
        r"The following antirequisites are only for students in the (Faculty of [^.]+)\.",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1), text


def _course_aliases(course_codes: list[str]) -> set[str]:
    aliases = {_normalize_course_code(code) for code in course_codes}
    aliases.update(code[:-1] for code in tuple(aliases) if code.endswith("E"))
    return aliases


def _normalize_course_code(course_code: str) -> str:
    return re.sub(r"\s+", "", course_code).upper()


def _failure(message: str, verification: str) -> dict[str, Any]:
    return {"can_take": False, "msg": message, "verification": verification}


def _manual_advisory(rule_name: str, detail: str) -> str:
    message = f"UWPath cannot verify this {rule_name} automatically"
    if detail:
        message += f": {detail}"
    return message
