"""Tests for the disruption-aware replanner."""
from __future__ import annotations

import pytest

from app.models import Company, Panel, Room, Student
from app.scheduler.replanner import build_replan_plan
from app.scheduler.types import (
    Assignment,
    CompanyInfo,
    PanelInfo,
    ProblemInput,
    RoomInfo,
)
from app.services import replanning_service, scheduling_service
from app.scheduler.validator import validate


def _small_problem() -> ProblemInput:
    companies = {
        "CA": CompanyInfo(id="CA", tier="TIER_1", duration_minutes=30,
                          panel_ids=["A1", "A2"], windows={"DAY_1": (540, 900)}),
    }
    panels = {
        "A1": PanelInfo(id="A1", company_id="CA", available_days={"DAY_1"}),
        "A2": PanelInfo(id="A2", company_id="CA", available_days={"DAY_1"}),
    }
    rooms = {"R1": RoomInfo(id="R1", available_days={"DAY_1"}),
             "R2": RoomInfo(id="R2", available_days={"DAY_1"})}
    current = {
        "I0": Assignment("I0", "S0", "CA", "DAY_1", 540, 20, "R1", "A1"),
        "I1": Assignment("I1", "S1", "CA", "DAY_1", 570, 20, "R2", "A2"),
        "I2": Assignment("I2", "S2", "CA", "DAY_1", 600, 20, "R1", "A1"),
    }
    return ProblemInput(
        interviews=[], companies=companies, rooms=rooms, panels=panels,
        original=dict(current), frozen={},
    )


def test_company_delay_marks_affected_interviews():
    # Post-disruption problem: company CA window on DAY_1 shifted to 10:00 (600).
    problem = _small_problem()
    problem.companies["CA"].windows["DAY_1"] = (600, 900)
    plan = build_replan_plan(problem.original, problem)
    # I0(540), I1(570) now fall before the window -> affected; I2(600) stays.
    assert plan.affected_ids == {"I0", "I1"}
    assert "I2" in plan.frozen
    assert plan.original["I0"].start == 540


def test_validity_based_partition():
    problem = _small_problem()
    # Make panel A1 unavailable for DAY_1 -> I0, I2 (on A1) affected.
    problem.panels["A1"].available_days = set()
    plan = build_replan_plan(problem.original, problem)
    assert plan.affected_ids == {"I0", "I2"}
    assert plan.frozen == {"I1": problem.original["I1"]}


@pytest.mark.usefixtures("_create_tables")
def test_all_four_disruptions_keep_schedule_valid(seeded_db):
    # Initial schedule
    scheduling_service.generate_schedule(seeded_db)
    current = replanning_service.load_active_assignments(seeded_db)
    assert len(current) > 0

    for disruption in _disruption_plans():
        entity_id = disruption["resolve"](seeded_db)
        replanning_service.apply_disruption(
            seeded_db, disruption["type"], entity_id, disruption["details"]
        )
        result = replanning_service.replan(seeded_db, disruption["reason"])
        assert result["schedule_status"] in ("PARTIAL", "FEASIBLE", "OPTIMAL")

        # Re-validate the new active schedule.
        new_current = replanning_service.load_active_assignments(seeded_db)
        ctx = scheduling_service.build_validation_context(seeded_db)
        reg = validate(list(new_current.values()), ctx)
        assert reg.valid, f"{disruption['type']}: {reg.violations}"


def _disruption_plans():
    return [
        {
            "type": "COMPANY_DELAY", "details": {"new_start_time": "12:00", "day": "DAY_1"},
            "reason": "delay",
            "resolve": lambda db: db.query(Company).order_by(Company.id).first().id,
        },
        {
            "type": "PANEL_UNAVAILABLE", "details": {},
            "reason": "panel",
            "resolve": lambda db: db.query(Panel).filter(Panel.status == "AVAILABLE").first().id,
        },
        {
            "type": "ROOM_UNAVAILABLE", "details": {},
            "reason": "room",
            "resolve": lambda db: db.query(Room).filter(Room.status == "AVAILABLE").first().id,
        },
        {
            "type": "STUDENT_WITHDRAWAL", "details": {},
            "reason": "withdraw",
            "resolve": lambda db: db.query(Student).filter(Student.status == "ACTIVE").first().id,
        },
    ]

