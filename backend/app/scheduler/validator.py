"""Independent post-solve schedule validator.

The solver output is never trusted blindly: after solving (and after the
room/panel coloring pass) the concrete assignment set is re-checked against
every hard constraint. If validation fails the schedule must not be published.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.scheduler.types import Assignment


@dataclass
class ValidationContext:
    # company_id -> day -> (start_min, end_min) [delay already applied]
    company_windows: dict[str, dict[str, tuple[int, int]]] = field(default_factory=dict)
    company_cutoff: dict[str, float] = field(default_factory=dict)
    # company_id -> day -> earliest allowed start (company delay)
    delay_min_start: dict[str, dict[str, int]] = field(default_factory=dict)
    student_status: dict[str, str] = field(default_factory=dict)
    student_cgpa: dict[str, float] = field(default_factory=dict)
    room_available_days: dict[str, set[str]] = field(default_factory=dict)
    panel_available_days: dict[str, set[str]] = field(default_factory=dict)
    panel_company: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationResult:
    valid: bool
    violations: list[dict] = field(default_factory=list)

    def add(self, code: str, message: str) -> None:
        self.violations.append({"code": code, "message": message})
        self.valid = False


def validate(assignments: list[Assignment], ctx: ValidationContext) -> ValidationResult:
    result = ValidationResult(valid=True)

    _check_overlaps(assignments, result, resource="student")
    _check_overlaps(assignments, result, resource="room")
    _check_overlaps(assignments, result, resource="panel")

    for a in assignments:
        _check_company_availability(a, ctx, result)
        _check_delay(a, ctx, result)
        _check_room_availability(a, ctx, result)
        _check_panel_availability(a, ctx, result)
        _check_eligibility(a, ctx, result)
        _check_withdrawal(a, ctx, result)

    return result


def _overlap(a: Assignment, b: Assignment) -> bool:
    return a.day == b.day and a.start < b.end and b.start < a.end


def _check_overlaps(
    assignments: list[Assignment], result: ValidationResult, resource: str
) -> None:
    by_resource: dict[str, list[Assignment]] = {}
    for a in assignments:
        key = getattr(a, f"{resource}_id")
        if key is None:
            continue
        by_resource.setdefault(key, []).append(a)

    for key, items in by_resource.items():
        items = sorted(items, key=lambda a: (a.day, a.start))
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if _overlap(items[i], items[j]):
                    result.add(
                        f"{resource.upper()}_OVERLAP",
                        f"{resource} {key} double-booked: {items[i].interview_id} "
                        f"({items[i].day} {items[i].start}) overlaps "
                        f"{items[j].interview_id} ({items[j].day} {items[j].start}).",
                    )
                    return


def _check_company_availability(a: Assignment, ctx: ValidationContext, result: ValidationResult) -> None:
    windows = ctx.company_windows.get(a.company_id, {})
    if a.day not in windows:
        result.add("COMPANY_UNAVAILABLE", f"{a.interview_id}: company {a.company_id} not available on {a.day}.")
        return
    start, end = windows[a.day]
    if a.start < start or a.end > end:
        result.add(
            "COMPANY_UNAVAILABLE",
            f"{a.interview_id}: {a.company_id} window is {start}-{end} but interview is {a.start}-{a.end}.",
        )


def _check_delay(a: Assignment, ctx: ValidationContext, result: ValidationResult) -> None:
    min_start = ctx.delay_min_start.get(a.company_id, {}).get(a.day)
    if min_start is not None and a.start < min_start:
        result.add(
            "COMPANY_DELAY",
            f"{a.interview_id}: {a.company_id} delayed until {min_start} on {a.day} but starts at {a.start}.",
        )


def _check_room_availability(a: Assignment, ctx: ValidationContext, result: ValidationResult) -> None:
    if a.room_id is None:
        result.add("NO_ROOM", f"{a.interview_id}: no room assigned.")
        return
    days = ctx.room_available_days.get(a.room_id, set())
    if a.day not in days:
        result.add("ROOM_UNAVAILABLE", f"{a.interview_id}: room {a.room_id} unavailable on {a.day}.")


def _check_panel_availability(a: Assignment, ctx: ValidationContext, result: ValidationResult) -> None:
    if a.panel_id is None:
        result.add("NO_PANEL", f"{a.interview_id}: no panel assigned.")
        return
    days = ctx.panel_available_days.get(a.panel_id, set())
    if a.day not in days:
        result.add("PANEL_UNAVAILABLE", f"{a.interview_id}: panel {a.panel_id} unavailable on {a.day}.")
        return
    if ctx.panel_company.get(a.panel_id) != a.company_id:
        result.add("PANEL_MISMATCH", f"{a.interview_id}: panel {a.panel_id} belongs to another company.")


def _check_eligibility(a: Assignment, ctx: ValidationContext, result: ValidationResult) -> None:
    cgpa = ctx.student_cgpa.get(a.student_id)
    cutoff = ctx.company_cutoff.get(a.company_id)
    if cgpa is not None and cutoff is not None and cgpa < cutoff:
        result.add(
            "INELIGIBLE",
            f"{a.interview_id}: student {a.student_id} CGPA {cgpa} below {a.company_id} cutoff {cutoff}.",
        )


def _check_withdrawal(a: Assignment, ctx: ValidationContext, result: ValidationResult) -> None:
    if ctx.student_status.get(a.student_id) == "WITHDRAWN":
        result.add("STUDENT_WITHDRAWN", f"{a.interview_id}: student {a.student_id} has withdrawn.")
