"""Database seeding from the deterministic generator."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.generator.placement_data import generate_data
from app.models import (
    AvailabilityWindow,
    Company,
    Panel,
    Room,
    Shortlist,
    Student,
)


def is_seeded(db: Session) -> bool:
    return db.query(Company).count() > 0


def seed_database(db: Session, seed: int = 42, force: bool = False) -> dict:
    """Generate deterministic data and persist it. Returns a summary."""
    if is_seeded(db) and not force:
        return _summary(db)

    if force:
        _clear(db)

    data = generate_data(seed)

    for c in data.companies:
        db.add(
            Company(
                id=c.id,
                name=c.name,
                priority_tier=c.priority_tier,
                cgpa_cutoff=c.cgpa_cutoff,
                interview_duration_minutes=c.interview_duration_minutes,
                panel_count=c.panel_count,
                available_days=c.available_days,
                availability_windows=c.availability_windows,
            )
        )

    for s in data.students:
        db.add(
            Student(
                id=s.id,
                name=s.name,
                cgpa=s.cgpa,
                branch=s.branch,
                year=s.year,
                status=s.status,
            )
        )

    for r in data.rooms:
        db.add(Room(id=r.id, name=r.name, status=r.status, capacity=r.capacity))

    for p in data.panels:
        db.add(Panel(id=p.id, company_id=p.company_id, name=p.name, status=p.status))

    now = datetime.now(timezone.utc)
    for sl in data.shortlists:
        db.add(
            Shortlist(
                id=sl.id,
                student_id=sl.student_id,
                company_id=sl.company_id,
                shortlisted_at=now,
            )
        )

    for w in data.availability_windows:
        db.add(
            AvailabilityWindow(
                resource_type=w.resource_type,
                resource_id=w.resource_id,
                date=datetime.strptime(w.date, "%Y-%m-%d").date(),
                start_time=w.start_time,
                end_time=w.end_time,
            )
        )

    db.commit()
    return _summary(db)


def _summary(db: Session) -> dict:
    return {
        "companies": db.query(Company).count(),
        "students": db.query(Student).count(),
        "rooms": db.query(Room).count(),
        "panels": db.query(Panel).count(),
        "shortlists": db.query(Shortlist).count(),
    }


def _clear(db: Session) -> None:
    from app.models import Disruption, Interview, ScheduleVersion

    for model in (Interview, Disruption, ScheduleVersion, AvailabilityWindow,
                  Shortlist, Panel, Room, Student, Company):
        db.query(model).delete()
    db.commit()
