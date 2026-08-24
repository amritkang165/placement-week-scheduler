"""Schedule API: generation, retrieval, metrics, and change diffs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.helpers import interview_to_out, version_to_out
from app.db.database import get_db
from app.db.seed import seed_database
from app.models import Company, Interview, Panel, Room, ScheduleVersion, Student
from app.schemas.schedule import (
    ConflictOut,
    GenerateDataRequest,
    MetricsOut,
    ScheduleRequest,
    ScheduleResponse,
    ScheduleVersionOut,
)
from app.scheduler.time_utils import date_to_day_key, time_str_to_minutes
from app.services import metrics_service, scheduling_service
from app.services.diff_service import diff_schedules
from app.services.replanning_service import _records_for_version

router = APIRouter(prefix="/api", tags=["schedule"])


@router.post("/generate-data")
def generate_data(req: GenerateDataRequest, db: Session = Depends(get_db)):
    return seed_database(db, seed=req.seed, force=req.force)


@router.post("/schedule")
def create_schedule(req: ScheduleRequest, db: Session = Depends(get_db)):
    if not db.query(Company).count():
        raise HTTPException(400, "No data. Generate data first.")
    version = scheduling_service.generate_schedule(db, req.reason)
    return version_to_out(db, version)


@router.get("/schedule", response_model=ScheduleResponse)
def get_schedule(db: Session = Depends(get_db)):
    version = db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).first()
    if version is None:
        raise HTTPException(404, "No schedule yet. Generate one first.")
    interviews = db.query(Interview).filter(Interview.schedule_version_id == version.id).all()
    return ScheduleResponse(
        version=version_to_out(db, version),
        interviews=[interview_to_out(db, iv) for iv in interviews],
    )


@router.get("/schedule/versions", response_model=list[ScheduleVersionOut])
def list_versions(db: Session = Depends(get_db)):
    versions = db.query(ScheduleVersion).order_by(ScheduleVersion.version_number.desc()).all()
    return [version_to_out(db, v) for v in versions]


@router.get("/schedule/metrics", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    version = db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).first()
    if version is None:
        raise HTTPException(404, "No schedule yet. Generate one first.")

    companies = {c.id: c for c in db.query(Company).all()}
    interviews = db.query(Interview).filter(Interview.schedule_version_id == version.id).all()

    scheduled_entries = []
    conflict_records = []
    scheduled_count = 0
    unscheduled_count = 0
    for iv in interviews:
        if iv.status == "SCHEDULED":
            scheduled_count += 1
            company = companies[iv.company_id]
            day_key = date_to_day_key(str(iv.date))
            start = time_str_to_minutes(iv.start_time)
            end = time_str_to_minutes(iv.end_time)
            scheduled_entries.append(
                (
                    iv.student_id,
                    iv.company_id,
                    day_key,
                    start,
                    end,
                    company.priority_tier,
                )
            )
            conflict_records.append(
                (iv.id, iv.student_id, iv.company_id, day_key, start, end, iv.room_id, iv.panel_id)
            )
        elif iv.status == "UNSCHEDULED":
            unscheduled_count += 1

    clashes = metrics_service.detect_conflicts(conflict_records)

    room_min, panel_min = scheduling_service.compute_capacity(db)

    moved_count = None
    previous_scheduled = None
    if version.previous_version_id:
        prev = db.get(ScheduleVersion, version.previous_version_id)
        if prev:
            old = _records_for_version(db, prev.id)
            new = _records_for_version(db, version.id)
            diff = diff_schedules(old, new, sum(1 for r in old.values() if r.status == "SCHEDULED"))
            moved_count = diff.summary["moved"]
            previous_scheduled = sum(1 for r in old.values() if r.status == "SCHEDULED")

    m = metrics_service.compute_metrics(
        scheduled=scheduled_entries,
        total=scheduled_count + unscheduled_count,
        room_available_minutes=room_min,
        panel_available_minutes=panel_min,
        solver_status=version.solver_status,
        schedule_status=version.schedule_status,
        moved_count=moved_count,
        previous_scheduled=previous_scheduled,
        student_clashes=len([c for c in clashes if c["type"] == "STUDENT_CLASH"]),
    )

    return MetricsOut(
        total=m.total,
        scheduled=m.scheduled,
        unscheduled=m.unscheduled,
        coverage=m.coverage,
        student_clashes=m.student_clashes,
        room_utilization=m.room_utilization,
        panel_utilization=m.panel_utilization,
        avg_wait_minutes=m.avg_wait_minutes,
        replan_churn=m.replan_churn,
        solver_status=m.solver_status,
        schedule_status=m.schedule_status,
        interviews_by_day=m.interviews_by_day,
        interviews_by_tier=m.interviews_by_tier,
        companies=db.query(Company).count(),
        students=db.query(Student).count(),
        rooms=db.query(Room).count(),
        panels=db.query(Panel).count(),
    )


@router.get("/schedule/conflicts", response_model=list[ConflictOut])
def get_conflicts(db: Session = Depends(get_db)):
    version = db.query(ScheduleVersion).filter(ScheduleVersion.is_active.is_(True)).first()
    if version is None:
        raise HTTPException(404, "No schedule yet. Generate one first.")
    records = [
        (
            iv.id,
            iv.student_id,
            iv.company_id,
            date_to_day_key(str(iv.date)),
            time_str_to_minutes(iv.start_time),
            time_str_to_minutes(iv.end_time),
            iv.room_id or "",
            iv.panel_id or "",
        )
        for iv in db.query(Interview)
        .filter(Interview.schedule_version_id == version.id, Interview.status == "SCHEDULED")
        .all()
    ]
    return metrics_service.detect_conflicts(records)


@router.get("/schedule/{version_id}", response_model=ScheduleResponse)
def get_schedule_version(version_id: str, db: Session = Depends(get_db)):
    version = db.get(ScheduleVersion, version_id)
    if version is None:
        raise HTTPException(404, "Schedule version not found.")
    interviews = db.query(Interview).filter(Interview.schedule_version_id == version.id).all()
    return ScheduleResponse(
        version=version_to_out(db, version),
        interviews=[interview_to_out(db, iv) for iv in interviews],
    )


@router.get("/schedule/{version_id}/changes")
def get_changes(version_id: str, db: Session = Depends(get_db)):
    from dataclasses import asdict

    version = db.get(ScheduleVersion, version_id)
    if version is None:
        raise HTTPException(404, "Schedule version not found.")
    prev = db.get(ScheduleVersion, version.previous_version_id) if version.previous_version_id else None
    if prev is None:
        return {"summary": {"affected_interviews": 0}, "changes": []}
    old = _records_for_version(db, prev.id)
    new = _records_for_version(db, version.id)
    old_scheduled = sum(1 for r in old.values() if r.status == "SCHEDULED")
    diff = diff_schedules(old, new, old_scheduled)
    return {
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
