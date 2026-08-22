#!/usr/bin/env python3
"""Placement-week demo scenarios.

Usage:
    python scripts/demo_scenarios.py                     # run the full live-defense sequence
    python scripts/demo_scenarios.py --scenario panel-failure
    python scripts/demo_scenarios.py --scenario company-delay
    python scripts/demo_scenarios.py --scenario room-failure
    python scripts/demo_scenarios.py --scenario student-withdrawal
    python scripts/demo_scenarios.py --scenario major-live-defense
    python scripts/demo_scenarios.py --seed 42
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal, engine  # noqa: E402
from app.db.seed import seed_database  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models import Company, Panel, Room, Student  # noqa: E402
from app.services import (  # noqa: E402
    replanning_service,
    scheduling_service,
)

SCENARIOS = {
    "company-delay",
    "panel-failure",
    "room-failure",
    "student-withdrawal",
    "major-live-defense",
}


def _banner(text: str) -> None:
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def initial_schedule(db) -> None:
    _banner("STEP 1 — Generate realistic dataset")
    print(scheduling_service.build_problem_from_db(db) and "Dataset present." or "Dataset present.")
    _banner("STEP 2 — Generate initial schedule")
    version = scheduling_service.generate_schedule(db)
    print(f"  {version.id}: {version.schedule_status} ({version.solver_status})")


def company_delay(db) -> None:
    _banner("DISRUPTION — Company delay")
    company = db.query(Company).first()
    replanning_service.apply_disruption(
        db, "COMPANY_DELAY", company.id, {"new_start_time": "12:00", "day": "DAY_1"}
    )
    _run_replan(db, f"{company.name} arrived late")

    _banner("PICKING A COMPANY DELAYED")
    print(f"  {company.name} ({company.id}) delayed until 12:00 on Day 1")


def panel_failure(db) -> None:
    _banner("DISRUPTION — Panel failure")
    panel = db.query(Panel).filter(Panel.status == "AVAILABLE").order_by(Panel.id).first()
    replanning_service.apply_disruption(db, "PANEL_UNAVAILABLE", panel.id, {})
    _run_replan(db, f"Panel {panel.id} unavailable")


def room_failure(db) -> None:
    _banner("DISRUPTION — Room failure")
    room = db.query(Room).filter(Room.status == "AVAILABLE").first()
    replanning_service.apply_disruption(db, "ROOM_UNAVAILABLE", room.id, {})
    _run_replan(db, f"Room {room.id} unavailable")


def student_withdrawal(db) -> None:
    _banner("DISRUPTION — Student withdrawals")
    students = db.query(Student).filter(Student.status == "ACTIVE").order_by(Student.id).limit(15).all()
    for s in students:
        replanning_service.apply_disruption(db, "STUDENT_WITHDRAWAL", s.id, {})
    _run_replan(db, "15 students withdrew")


def major_live_defense(db) -> None:
    _banner("MAJOR LIVE-DEFENSE SCENARIO")
    print("A major Day-1 recruiter is 3 hours late, one of its panels dropped,")
    print("and 15 students withdrew. Applying all disruptions...")

    # Pick a TIER_1 company that is a mass recruiter.
    company = (
        db.query(Company)
        .filter(Company.priority_tier == "TIER_1")
        .order_by(Company.id)
        .first()
    )
    print(f"\n  Recruiter: {company.name} ({company.id})")
    replanning_service.apply_disruption(
        db, "COMPANY_DELAY", company.id, {"new_start_time": "14:00", "day": "DAY_1"}
    )

    # Drop one of its panels.
    panel = db.query(Panel).filter(Panel.company_id == company.id).first()
    print(f"  Panel dropped: {panel.id}")
    replanning_service.apply_disruption(db, "PANEL_UNAVAILABLE", panel.id, {})

    # Withdraw 15 students.
    students = db.query(Student).filter(Student.status == "ACTIVE").order_by(Student.id).limit(15).all()
    print(f"  Students withdrawn: {len(students)}")
    for s in students:
        replanning_service.apply_disruption(db, "STUDENT_WITHDRAWAL", s.id, {})

    _run_replan(db, "Major Day-1 recruiter late + panel drop + 15 withdrawals")


def _run_replan(db, reason: str) -> None:
    result = replanning_service.replan(db, reason)
    s = result["summary"]
    _banner("REPLAN COMPLETE")
    print(f"  Version: {result['version_id']} -> {result['reason']}")
    print(f"  Solver: {result['solver_status']} | Schedule: {result['schedule_status']}")
    print(f"\n  Affected interviews : {s['affected_interviews']}")
    print(f"  Moved               : {s['moved']}")
    print(f"  Cancelled           : {s['cancelled']}")
    print(f"  Added               : {s['added']}")
    print(f"  Unchanged           : {s['unchanged']}")
    print(f"  Unscheduled         : {s['unscheduled']}")
    print(f"  Students affected   : {s['students_affected']}")
    print(f"  Rooms affected      : {s['rooms_affected']}")
    print(f"  Panels affected     : {s['panels_affected']}")
    print(f"  Replan churn        : {s['replan_churn']}%")

    # Show a few example changes.
    for change in result["changes"][:4]:
        if change["change_type"] in ("MOVED", "CANCELLED", "ADDED"):
            b = change["before"] or {}
            a = change["after"] or {}
            print(
                f"    {change['change_type']:9s} {change['student_name']:20s} "
                f"{change['company_name'][:20]:20s} "
                f"{(b.get('start') or '-'):5s}->{(a.get('start') or '-'):5s}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Placement scheduler demo scenarios.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="major-live-defense")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db, seed=args.seed, force=True)
        if args.scenario == "company-delay":
            initial_schedule(db)
            company_delay(db)
        elif args.scenario == "panel-failure":
            initial_schedule(db)
            panel_failure(db)
        elif args.scenario == "room-failure":
            initial_schedule(db)
            room_failure(db)
        elif args.scenario == "student-withdrawal":
            initial_schedule(db)
            student_withdrawal(db)
        else:
            initial_schedule(db)
            major_live_defense(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
