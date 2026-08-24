"""Serialization helpers shared by the API routers."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Company, Interview, Student
from app.schemas.interview import InterviewOut
from app.schemas.schedule import ScheduleVersionOut


def interview_to_out(db: Session, iv: Interview) -> InterviewOut:
    student = db.get(Student, iv.student_id)
    company = db.get(Company, iv.company_id)
    return InterviewOut(
        id=iv.id,
        student_id=iv.student_id,
        student_name=student.name if student else iv.student_id,
        company_id=iv.company_id,
        company_name=company.name if company else iv.company_id,
        room_id=iv.room_id,
        panel_id=iv.panel_id,
        date=str(iv.date) if iv.date else None,
        start_time=iv.start_time,
        end_time=iv.end_time,
        duration_minutes=iv.duration_minutes,
        status=iv.status,
        reason=iv.reason,
    )


def version_to_out(db: Session, version) -> ScheduleVersionOut:
    interviews = db.query(Interview).filter(Interview.schedule_version_id == version.id).all()
    return ScheduleVersionOut(
        id=version.id,
        version_number=version.version_number,
        reason=version.reason,
        previous_version_id=version.previous_version_id,
        solver_status=version.solver_status,
        schedule_status=version.schedule_status,
        is_active=version.is_active,
        created_at=version.created_at,
        scheduled_count=sum(1 for i in interviews if i.status == "SCHEDULED"),
        unscheduled_count=sum(1 for i in interviews if i.status == "UNSCHEDULED"),
        cancelled_count=sum(1 for i in interviews if i.status == "CANCELLED"),
    )
