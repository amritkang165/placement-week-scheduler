"""Disruption-aware replanner.

The replanner does NOT blindly re-run the scheduler from scratch. It follows:

    current schedule
        -> identify interviews invalidated by the disruption
        -> freeze unaffected appointments
        -> free the affected assignments
        -> re-optimize the affected region (with move penalties)
        -> validate + diff (handled by services)

Freezing is the key anti-churn mechanism: only interviews that become invalid
because of the post-disruption state are allowed to move. Everything else is
pinned to its existing (day, start, room, panel).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.scheduler.types import Assignment, ProblemInput


@dataclass
class DisruptionSpec:
    type: str  # COMPANY_DELAY | PANEL_UNAVAILABLE | ROOM_UNAVAILABLE | STUDENT_WITHDRAWAL
    entity_id: str
    details: dict = field(default_factory=dict)


@dataclass
class ReplanPlan:
    """Result of deciding what is frozen vs free for a replan."""

    affected_ids: set[str] = field(default_factory=set)
    frozen: dict[str, Assignment] = field(default_factory=dict)
    original: dict[str, Assignment] = field(default_factory=dict)


def build_replan_plan(
    current: dict[str, Assignment],
    problem: ProblemInput,
    disruption: DisruptionSpec | None = None,
) -> ReplanPlan:
    """Partition current assignments into affected (free) vs frozen.

    An assignment is affected if it is no longer valid under the post-
    disruption problem state (its company window no longer covers its time, its
    room/panel is unavailable, or its student withdrew). `problem` must already
    reflect the post-disruption state.
    """
    plan = ReplanPlan()

    for interview_id, a in current.items():
        if _valid_in_problem(a, problem):
            plan.frozen[interview_id] = a
        else:
            plan.affected_ids.add(interview_id)
        plan.original[interview_id] = a

    return plan


def _valid_in_problem(a: Assignment, problem: ProblemInput) -> bool:
    company = problem.companies.get(a.company_id)
    if company is None:
        return False
    win = company.windows.get(a.day)
    if win is None:
        return False
    ws, we = win
    if a.start < ws or a.end > we:
        return False
    if a.room_id is not None:
        room = problem.rooms.get(a.room_id)
        if room is None or a.day not in room.available_days:
            return False
    if a.panel_id is not None:
        panel = problem.panels.get(a.panel_id)
        if panel is None or a.day not in panel.available_days:
            return False
    return True
