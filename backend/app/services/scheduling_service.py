"""Scheduling service: builds the CP-SAT problem from DB state, solves,
validates, and persists a new schedule version.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import solver_config
from app.models import (
    Company,
    Disruption,
    Interview,
    Panel,
    Room,
    ScheduleVersion,
    Shortlist,
    Student,
)
from app.scheduler.solver import solve
from app.scheduler.time_utils import (
    DAY_DATES,
    DAY_KEYS,
    OPERATING_END_MIN,
    OPERATING_START_MIN,
    minutes_to_time_str,
    time_str_to_minutes,
)
from app.scheduler.types import (
    Assignment,
    CompanyInfo,
    InterviewRequirement,
    PanelInfo,
    ProblemInput,
    RoomInfo,
    Solution,
)
from app.scheduler.validator import ValidationContext


class ScheduleValidationError(RuntimeError):
    """Raised when solver output fails post-solve validation."""


def _active_delays(db: Session) -> dict[str, dict[str, int]]:
    """Active company-delay constraints: company_id -> {day: earliest start (min)}.

    Supports two detail schemas:
      * specific day: ``{"day": DAY_KEY, "new_start_time": "HH:MM"}``
      * global shift: ``{"delay_hours": N}`` (pulls every window's start in by N hours)
    """
    delay: dict[str, dict[str, int]] = {}
    for d in db.query(Disruption).filter(Disruption.status == "ACTIVE").all():
        if d.type != "COMPANY_DELAY":
            continue
        company = db.get(Company, d.entity_id)
        day = d.details.get("day")
        new_start = d.details.get("new_start_time")
        if day and new_start:
            delay.setdefault(d.entity_id, {})[day] = time_str_to_minutes(new_start)
            continue
        hours = d.details.get("delay_hours")
        if hours is None or company is None:
            continue
        shift = int(hours) * 60
        targets = delay.setdefault(d.entity_id, {})
        for w in company.availability_windows or []:
            start = time_str_to_minutes(w["start"])
            end = time_str_to_minutes(w["end"])
            targets[w["day"]] = min(start + shift, end)
    return delay


def build_problem_from_db(db: Session) -> ProblemInput:
    companies = {c.id: c for c in db.query(Company).all()}
    students = {s.id: s for s in db.query(Student).all()}
    rooms = {r.id: r for r in db.query(Room).all()}
    panels = {p.id: p for p in db.query(Panel).all()}
    shortlists = db.query(Shortlist).all()
    delay = _active_delays(db)

    company_info: dict[str, CompanyInfo] = {}
    for c in companies.values():
        windows: dict[str, tuple[int, int]] = {}
        for w in c.availability_windows or []:
            windows[w["day"]] = (
                time_str_to_minutes(w["start"]),
                time_str_to_minutes(w["end"]),
            )
        for day, min_start in delay.get(c.id, {}).items():
            if day in windows:
                start, end = windows[day]
                windows[day] = (max(start, min_start), end)
        company_info[c.id] = CompanyInfo(
            id=c.id,
            tier=c.priority_tier,
            duration_minutes=c.interview_duration_minutes,
            panel_ids=[p.id for p in panels.values() if p.company_id == c.id],
            windows=windows,
        )

    room_info: dict[str, RoomInfo] = {}
    for r in rooms.values():
        room_info[r.id] = RoomInfo(
            id=r.id,
            available_days=set(DAY_KEYS) if r.status == "AVAILABLE" else set(),
        )

    panel_info: dict[str, PanelInfo] = {}
    for p in panels.values():
        comp = companies[p.company_id]
        panel_info[p.id] = PanelInfo(
            id=p.id,
            company_id=p.company_id,
            available_days=set(comp.available_days or []) if p.status == "AVAILABLE" else set(),
        )

    interviews: list[InterviewRequirement] = []
    for sl in shortlists:
        if students[sl.student_id].status == "WITHDRAWN":
            continue
        c = companies[sl.company_id]
        interviews.append(
            InterviewRequirement(
                id=sl.id,
                student_id=sl.student_id,
                company_id=sl.company_id,
                duration_minutes=c.interview_duration_minutes,
                tier=c.priority_tier,
            )
        )

    return ProblemInput(
        interviews=interviews,
        companies=company_info,
        rooms=room_info,
        panels=panel_info,
    )


def build_validation_context(db: Session) -> ValidationContext:
    companies = {c.id: c for c in db.query(Company).all()}
    students = {s.id: s for s in db.query(Student).all()}
    rooms = {r.id: r for r in db.query(Room).all()}
    panels = {p.id: p for p in db.query(Panel).all()}
    delay = _active_delays(db)

    ctx = ValidationContext(
        student_status={s.id: s.status for s in students.values()},
        student_cgpa={s.id: s.cgpa for s in students.values()},
        panel_company={p.id: p.company_id for p in panels.values()},
    )
    for c in companies.values():
        windows = {
            w["day"]: (time_str_to_minutes(w["start"]), time_str_to_minutes(w["end"]))
            for w in (c.availability_windows or [])
        }
        ctx.company_windows[c.id] = windows
        ctx.company_cutoff[c.id] = c.cgpa_cutoff
        ctx.delay_min_start[c.id] = delay.get(c.id, {})
    for r in rooms.values():
        ctx.room_available_days[r.id] = set(DAY_KEYS) if r.status == "AVAILABLE" else set()
    for p in panels.values():
        ctx.panel_available_days[p.id] = (
            set(companies[p.company_id].available_days or [])
            if p.status == "AVAILABLE"
            else set()
        )
    return ctx


def compute_capacity(db: Session) -> tuple[int, int]:
    rooms = db.query(Room).filter(Room.status == "AVAILABLE").count()
    companies = {c.id: c for c in db.query(Company).all()}
    panels = db.query(Panel).filter(Panel.status == "AVAILABLE").all()

    day_min = OPERATING_END_MIN - OPERATING_START_MIN
    room_min = rooms * len(DAY_KEYS) * day_min
    panel_min = sum(len(companies[p.company_id].available_days or []) * day_min for p in panels)
    return room_min, panel_min


def schedule_status_for(solver_status: str, unscheduled: int) -> str:
    if solver_status == "INFEASIBLE":
        return "INFEASIBLE"
    if unscheduled == 0:
        return solver_status if solver_status in ("OPTIMAL", "FEASIBLE") else "FEASIBLE"
    return "PARTIAL"


def diagnose_unscheduled(req: InterviewRequirement, problem: ProblemInput, solution: Solution) -> str:
    company = problem.companies[req.company_id]
    days = [d for d in DAY_KEYS if d in company.windows]
    if not days:
        return "COMPANY_UNAVAILABLE"

    any_panel = any(
        p.company_id == req.company_id and any(d in p.available_days for d in days)
        for p in problem.panels.values()
    )
    if not any_panel:
        return "NO_PANEL"

    any_room = any(any(d in r.available_days for d in days) for r in problem.rooms.values())
    if not any_room:
        return "NO_ROOM"

    scheduled = [a for a in solution.assignments.values() if a.student_id == req.student_id]
    for d in days:
        ws, we = company.windows[d]
        if _has_free_slot(ws, we, scheduled, d, req.duration_minutes):
            return "NO_FEASIBLE_SLOT"
    return "STUDENT_CONFLICT"


def _has_free_slot(ws: int, we: int, scheduled: list[Assignment], day: str, duration: int) -> bool:
    busy = sorted([(a.start, a.end) for a in scheduled if a.day == day], key=lambda x: x[0])
    cursor = ws
    for s, e in busy:
        if s > cursor and s - cursor >= duration:
            return True
        cursor = max(cursor, e)
    return we - cursor >= duration


def next_version_number(db: Session) -> int:
    current = db.query(ScheduleVersion).order_by(ScheduleVersion.version_number.desc()).first()
    return (current.version_number + 1) if current else 1


def persist_schedule(
    db: Session,
    problem: ProblemInput,
    solution: Solution,
    reason: str,
    previous_version_id: str | None = None,
) -> ScheduleVersion:
    """Persist a new (validated) schedule version and its interview rows."""
    # Deactivate any previous active version.
    for v in db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).all():
        v.is_active = False

    unscheduled_count = len(problem.interviews) - len(solution.assignments)
    vnum = next_version_number(db)
    version = ScheduleVersion(
        id=f"SCH-{vnum:03d}",
        version_number=vnum,
        reason=reason,
        previous_version_id=previous_version_id,
        solver_status=solution.solver_status,
        schedule_status=schedule_status_for(solution.solver_status, unscheduled_count),
        is_active=True,
    )
    db.add(version)
    db.flush()

    students = {s.id: s for s in db.query(Student).all()}
    scheduled_ids = set(solution.assignments.keys())

    for req in problem.interviews:
        a = solution.assignments.get(req.id)
        if a is not None:
            db.add(
                Interview(
                    id=req.id,
                    schedule_version_id=version.id,
                    student_id=req.student_id,
                    company_id=req.company_id,
                    room_id=a.room_id,
                    panel_id=a.panel_id,
                    date=datetime.strptime(DAY_DATES[a.day], "%Y-%m-%d").date(),
                    start_time=minutes_to_time_str(a.start),
                    end_time=minutes_to_time_str(a.end),
                    duration_minutes=req.duration_minutes,
                    status="SCHEDULED",
                )
            )
        else:
            db.add(
                Interview(
                    id=req.id,
                    schedule_version_id=version.id,
                    student_id=req.student_id,
                    company_id=req.company_id,
                    duration_minutes=req.duration_minutes,
                    status="UNSCHEDULED",
                    reason=diagnose_unscheduled(req, problem, solution),
                )
            )

    # Withdrawn students: cancel their remaining shortlist edges explicitly.
    withdrawn_shortlists = (
        db.query(Shortlist)
        .join(Student, Shortlist.student_id == Student.id)
        .filter(Student.status == "WITHDRAWN")
        .all()
    )
    for sl in withdrawn_shortlists:
        db.add(
            Interview(
                id=sl.id,
                schedule_version_id=version.id,
                student_id=sl.student_id,
                company_id=sl.company_id,
                duration_minutes=db.query(Company)
                .filter(Company.id == sl.company_id)
                .first()
                .interview_duration_minutes,
                status="CANCELLED",
                reason="STUDENT_WITHDRAWN",
            )
        )

    db.commit()
    db.refresh(version)
    return version


def generate_schedule(db: Session, reason: str = "Initial schedule") -> ScheduleVersion:
    """Full initial-scheduling flow: build, solve, validate, persist."""
    from app.scheduler.validator import validate

    problem = build_problem_from_db(db)
    solution = solve(problem, solver_config)

    result = validate(list(solution.assignments.values()), build_validation_context(db))
    if not result.valid:
        raise ScheduleValidationError(
            "Solver produced an invalid schedule: " + "; ".join(v["message"] for v in result.violations)
        )

    return persist_schedule(db, problem, solution, reason)

