"""Tests for the CP-SAT scheduler."""
from __future__ import annotations

from app.config import SolverConfig
from app.scheduler.solver import solve
from app.scheduler.types import (
    CompanyInfo,
    InterviewRequirement,
    PanelInfo,
    ProblemInput,
    RoomInfo,
)


def _small_problem() -> ProblemInput:
    """2 companies, 8 students, 4 rooms, panel capacity 2 each."""
    interviews = []
    companies = {}
    panels = {}
    # Company A: 4 interviews, 2 panels. Company B: 4 interviews, 2 panels.
    for company_id, panel_base in (("CA", "A"), ("CB", "B")):
        companies[company_id] = CompanyInfo(
            id=company_id, tier="TIER_1", duration_minutes=30,
            panel_ids=[f"{panel_base}1", f"{panel_base}2"],
            windows={"DAY_1": (540, 900)},
        )
        panels[f"{panel_base}1"] = PanelInfo(id=f"{panel_base}1", company_id=company_id, available_days={"DAY_1"})
        panels[f"{panel_base}2"] = PanelInfo(id=f"{panel_base}2", company_id=company_id, available_days={"DAY_1"})
        for i in range(4):
            interviews.append(
                InterviewRequirement(
                    id=f"{company_id}-{i}", student_id=f"S{i}", company_id=company_id,
                    duration_minutes=30, tier="TIER_1",
                )
            )
    rooms = {f"R{i}": RoomInfo(id=f"R{i}", available_days={"DAY_1"}) for i in range(4)}
    return ProblemInput(interviews=interviews, companies=companies, rooms=rooms, panels=panels)


def test_scheduler_solves_and_assigns_everything():
    problem = _small_problem()
    sol = solve(problem, SolverConfig(time_limit_seconds=2.0, num_search_workers=2))
    # 8 interviews, capacity is ample -> all scheduled.
    assert len(sol.assignments) == 8
    assert sol.solver_status in ("OPTIMAL", "FEASIBLE")


def test_scheduler_no_overlaps():
    problem = _small_problem()
    sol = solve(problem, SolverConfig(time_limit_seconds=2.0, num_search_workers=2))
    from collections import defaultdict

    for resource in ("student", "room", "panel"):
        groups = defaultdict(list)
        for a in sol.assignments.values():
            groups[getattr(a, f"{resource}_id")].append((a.start, a.end))
        for key, ivs in groups.items():
            ivs = sorted(ivs)
            assert ivs[0][0] >= 540
            for i in range(len(ivs) - 1):
                assert ivs[i][1] <= ivs[i + 1][0], f"{resource} {key} overlap"


def test_full_dataset_end_to_end():
    from app.generator.placement_data import generate_data
    from app.scheduler.types import CompanyInfo, PanelInfo, RoomInfo
    from app.scheduler.time_utils import DAY_KEYS, time_str_to_minutes
    from app.scheduler.validator import ValidationContext, validate

    data = generate_data(seed=42)
    companies = {}
    for c in data.companies:
        windows = {
            w["day"]: (time_str_to_minutes(w["start"]), time_str_to_minutes(w["end"]))
            for w in c.availability_windows
        }
        companies[c.id] = CompanyInfo(
            id=c.id, tier=c.priority_tier, duration_minutes=c.interview_duration_minutes,
            panel_ids=[p.id for p in data.panels if p.company_id == c.id], windows=windows,
        )
    rooms = {r.id: RoomInfo(id=r.id, available_days=set(DAY_KEYS)) for r in data.rooms}
    panels = {p.id: PanelInfo(id=p.id, company_id=p.company_id, available_days=set(DAY_KEYS))
              for p in data.panels}
    interviews = [
        InterviewRequirement(
            id=sl.id, student_id=sl.student_id, company_id=sl.company_id,
            duration_minutes=companies[sl.company_id].duration_minutes,
            tier=companies[sl.company_id].tier,
        )
        for sl in data.shortlists
    ]
    problem = ProblemInput(interviews=interviews, companies=companies, rooms=rooms, panels=panels)
    sol = solve(problem, SolverConfig(time_limit_seconds=3.0, num_search_workers=4))
    assert len(sol.assignments) > 0

    ctx = ValidationContext(
        company_windows={c.id: c.windows for c in companies.values()},
        company_cutoff={c.id: c.cgpa_cutoff for c in data.companies},
        student_status={s.id: s.status for s in data.students},
        student_cgpa={s.id: s.cgpa for s in data.students},
        room_available_days={r.id: set(DAY_KEYS) for r in data.rooms},
        panel_available_days={p.id: set(DAY_KEYS) for p in data.panels},
        panel_company={p.id: p.company_id for p in data.panels},
    )
    result = validate(list(sol.assignments.values()), ctx)
    assert result.valid, result.violations
    # Capacity limits: room util cannot exceed 100%.
    used = sum(a.end - a.start for a in sol.assignments.values())
    assert used <= 20 * 480 * 4
