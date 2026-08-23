"""Replanning service: applies disruptions to DB state and re-optimizes the
affected region of the schedule (freezing unaffected appointments).
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import solver_config
from app.models import Company, Disruption, Interview, Panel, Room, ScheduleVersion, Student
from app.scheduler.replanner import build_replan_plan
from app.scheduler.solver import solve
from app.scheduler.time_utils import date_to_day_key, time_str_to_minutes
from app.scheduler.types import Assignment
from app.scheduler.validator import validate
from app.services.diff_service import DiffResult, InterviewRecord, diff_schedules
from app.services.scheduling_service import (
    ScheduleValidationError,
    build_problem_from_db,
    build_validation_context,
    persist_schedule,
)


def apply_disruption(db: Session, type_: str, entity_id: str, details: dict) -> Disruption:
    """Record a disruption and update the affected entity's state."""
    if type_ == "COMPANY_DELAY":
        company = db.get(Company, entity_id)
        if company is None:
            raise ValueError(f"Company {entity_id} not found")
        company.delayed_until = details.get("new_start_time") or details.get("delay_hours")

    elif type_ == "PANEL_UNAVAILABLE":
        panel = db.get(Panel, entity_id)
        if panel is None:
            raise ValueError(f"Panel {entity_id} not found")
        panel.status = "UNAVAILABLE"

    elif type_ == "ROOM_UNAVAILABLE":
        room = db.get(Room, entity_id)
        if room is None:
            raise ValueError(f"Room {entity_id} not found")
        room.status = "UNAVAILABLE"

    elif type_ == "STUDENT_WITHDRAWAL":
        student = db.get(Student, entity_id)
        if student is None:
            raise ValueError(f"Student {entity_id} not found")
        student.status = "WITHDRAWN"

    else:
        raise ValueError(f"Unknown disruption type: {type_}")

    active = db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).first()
    eff = details.get("effective_from")
    disruption = Disruption(
        id=f"DIS-{_next_disruption_num(db):03d}",
        type=type_,
        entity_id=entity_id,
        effective_from=datetime.fromisoformat(eff) if eff else datetime.now(timezone.utc),
        details=details,
        status="ACTIVE",
        schedule_version_id=active.id if active else None,
    )
    db.add(disruption)
    db.commit()
    db.refresh(disruption)
    return disruption


def _next_disruption_num(db: Session) -> int:
    current = db.query(Disruption).order_by(Disruption.id.desc()).first()
    if current is None:
        return 1
    try:
        return int(current.id.split("-")[1]) + 1
    except (IndexError, ValueError):
        return db.query(Disruption).count() + 1


def load_active_assignments(db: Session) -> dict[str, Assignment]:
    active = db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).first()
    if active is None:
        return {}
    out: dict[str, Assignment] = {}
    for iv in db.query(Interview).filter(
        Interview.schedule_version_id == active.id, Interview.status == "SCHEDULED"
    ).all():
        out[iv.id] = Assignment(
            interview_id=iv.id,
            student_id=iv.student_id,
            company_id=iv.company_id,
            day=date_to_day_key(str(iv.date)),
            start=time_str_to_minutes(iv.start_time),
            duration=iv.duration_minutes,
            room_id=iv.room_id,
            panel_id=iv.panel_id,
        )
    return out


def _records_for_version(db: Session, version_id: str) -> dict[str, InterviewRecord]:
    companies = {c.id: c.name for c in db.query(Company).all()}
    students = {s.id: s.name for s in db.query(Student).all()}
    out: dict[str, InterviewRecord] = {}
    for iv in db.query(Interview).filter(Interview.schedule_version_id == version_id).all():
        out[iv.id] = InterviewRecord(
            id=iv.id,
            student_id=iv.student_id,
            student_name=students.get(iv.student_id, iv.student_id),
            company_id=iv.company_id,
            company_name=companies.get(iv.company_id, iv.company_id),
            status=iv.status,
            date=str(iv.date) if iv.date else None,
            start_time=iv.start_time,
            end_time=iv.end_time,
            room_id=iv.room_id,
            panel_id=iv.panel_id,
            reason=iv.reason,
        )
    return out


def replan(db: Session, reason: str = "Replan after disruption") -> dict:
    """Run the disruption-aware replan and return a structured result."""
    active = db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).first()
    if active is None:
        raise ValueError("No active schedule to replan. Generate a schedule first.")

    current = load_active_assignments(db)
    problem = build_problem_from_db(db)

    plan = build_replan_plan(current, problem)
    affected = plan.affected_ids

    problem.original = dict(current)
    problem.frozen = dict(plan.frozen)

    solution = solve(problem, solver_config)

    result = validate(list(solution.assignments.values()), build_validation_context(db))
    if not result.valid:
        raise ScheduleValidationError(
            "Replan produced an invalid schedule: "
            + "; ".join(v["message"] for v in result.violations)
        )

    old_records = _records_for_version(db, active.id)
    old_scheduled = sum(1 for r in old_records.values() if r.status == "SCHEDULED")

    new_version = persist_schedule(
        db, problem, solution, reason, previous_version_id=active.id
    )
    new_records = _records_for_version(db, new_version.id)

    diff: DiffResult = diff_schedules(old_records, new_records, old_scheduled)

    # Mark disruptions as processed.
    for d in db.query(Disruption).filter(Disruption.status == "ACTIVE").all():
        d.status = "RESOLVED"
        d.schedule_version_id = new_version.id
    db.commit()

    return {
        "version_id": new_version.id,
        "version_number": new_version.version_number,
        "solver_status": new_version.solver_status,
        "schedule_status": new_version.schedule_status,
        "reason": new_version.reason,
        "summary": diff.summary,
        "changes": [
            {
                "interview_id": i.interview_id,
                "student_id": i.student_id,
                "student_name": i.student_name,
                "company_id": i.company_id,
                "company_name": i.company_name,
                "change_type": i.change_type,
                "before": asdict(i.before) if i.before else None,
                "after": asdict(i.after) if i.after else None,
                "reason": i.reason,
            }
            for i in diff.items
        ],
    }
