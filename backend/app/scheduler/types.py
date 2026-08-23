"""Pure dataclasses shared across the scheduler, replanner, validator and services.

These are deliberately decoupled from SQLAlchemy ORM models so the solver can
run standalone (and be unit-tested) without a database.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InterviewRequirement:
    id: str
    student_id: str
    company_id: str
    duration_minutes: int
    tier: str


@dataclass
class CompanyInfo:
    id: str
    tier: str
    duration_minutes: int
    panel_ids: list[str]
    # day_key -> (start_min, end_min) operating window (delay already applied)
    windows: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class RoomInfo:
    id: str
    available_days: set[str] = field(default_factory=set)


@dataclass
class PanelInfo:
    id: str
    company_id: str
    available_days: set[str] = field(default_factory=set)


@dataclass
class Assignment:
    interview_id: str
    student_id: str
    company_id: str
    day: str
    start: int
    duration: int
    room_id: str | None = None
    panel_id: str | None = None

    @property
    def end(self) -> int:
        return self.start + self.duration


@dataclass
class ProblemInput:
    interviews: list[InterviewRequirement]
    companies: dict[str, CompanyInfo] = field(default_factory=dict)
    rooms: dict[str, RoomInfo] = field(default_factory=dict)
    panels: dict[str, PanelInfo] = field(default_factory=dict)
    operating_start: int = 9 * 60
    operating_end: int = 17 * 60
    # Replanning support: previous assignment (to penalize movement) and
    # assignments that must remain exactly frozen.
    original: dict[str, Assignment] = field(default_factory=dict)
    frozen: dict[str, Assignment] = field(default_factory=dict)


@dataclass
class Solution:
    # interview_id -> Assignment for every scheduled interview.
    assignments: dict[str, Assignment] = field(default_factory=dict)
    solver_status: str = "UNKNOWN"  # OPTIMAL / FEASIBLE / INFEASIBLE / UNKNOWN
    wall_time_seconds: float = 0.0
    objective_value: float = 0.0


def problem_days(problem: ProblemInput) -> list[str]:
    """All placement-day keys referenced by the problem, in canonical order."""
    days: set[str] = set()
    for c in problem.companies.values():
        days.update(c.windows.keys())
    for r in problem.rooms.values():
        days.update(r.available_days)
    for p in problem.panels.values():
        days.update(p.available_days)
    for a in list(problem.original.values()) + list(problem.frozen.values()):
        days.add(a.day)
    return sorted(days)
