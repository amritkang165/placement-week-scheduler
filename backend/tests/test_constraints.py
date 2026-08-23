"""Tests for the validator (hard constraints) and slot generation."""
from __future__ import annotations

from app.scheduler.slot_generator import candidate_starts, day_time_grid
from app.scheduler.types import Assignment
from app.scheduler.validator import ValidationContext, ValidationResult, validate


def _ctx(**overrides) -> ValidationContext:
    ctx = ValidationContext(
        company_windows={"C1": {"DAY_1": (540, 1020)}},
        company_cutoff={"C1": 7.0},
        delay_min_start={},
        student_status={"S1": "ACTIVE", "S2": "ACTIVE"},
        student_cgpa={"S1": 8.0, "S2": 6.5},
        room_available_days={"ROOM-01": {"DAY_1"}},
        panel_available_days={"P1": {"DAY_1"}},
        panel_company={"P1": "C1"},
    )
    ctx.__dict__.update(overrides)
    return ctx


def _iv(iid, student, day="DAY_1", start=540, dur=30, room="ROOM-01", panel="P1"):
    return Assignment(
        interview_id=iid, student_id=student, company_id="C1",
        day=day, start=start, duration=dur, room_id=room, panel_id=panel,
    )


def test_student_overlap_detected():
    ctx = _ctx()
    ivs = [_iv("I1", "S1", start=540), _iv("I2", "S1", start=555)]
    res = validate(ivs, ctx)
    assert not res.valid
    assert any(v["code"] == "STUDENT_OVERLAP" for v in res.violations)


def test_room_overlap_detected():
    ctx = _ctx()
    ivs = [_iv("I1", "S1", start=540), _iv("I2", "S2", start=555)]
    res = validate(ivs, ctx)
    assert not res.valid
    assert any(v["code"] == "ROOM_OVERLAP" for v in res.violations)


def test_panel_overlap_detected():
    ctx = _ctx()
    ivs = [_iv("I1", "S1", start=540, room="ROOM-01"), _iv("I2", "S2", start=555, room="ROOM-02")]
    ctx.room_available_days["ROOM-02"] = {"DAY_1"}
    res = validate(ivs, ctx)
    assert not res.valid
    assert any(v["code"] == "PANEL_OVERLAP" for v in res.violations)


def test_cgpa_ineligibility_detected():
    ctx = _ctx()
    res = validate([_iv("I1", "S2")], ctx)  # S2 cgpa 6.5 < cutoff 7.0
    assert not res.valid
    assert any(v["code"] == "INELIGIBLE" for v in res.violations)


def test_company_availability_detected():
    ctx = _ctx(company_windows={"C1": {"DAY_1": (540, 600)}})
    res = validate([_iv("I1", "S1", start=600)], ctx)  # ends 630 > 600
    assert not res.valid
    assert any(v["code"] == "COMPANY_UNAVAILABLE" for v in res.violations)


def test_delay_detected():
    ctx = _ctx(delay_min_start={"C1": {"DAY_1": 660}})
    res = validate([_iv("I1", "S1", start=540)], ctx)  # before 660
    assert not res.valid
    assert any(v["code"] == "COMPANY_DELAY" for v in res.violations)


def test_withdrawal_detected():
    ctx = _ctx(student_status={"S1": "WITHDRAWN"})
    res = validate([_iv("I1", "S1")], ctx)
    assert not res.valid
    assert any(v["code"] == "STUDENT_WITHDRAWN" for v in res.violations)


def test_room_unavailable_detected():
    ctx = _ctx(room_available_days={"ROOM-01": set()})
    res = validate([_iv("I1", "S1")], ctx)
    assert not res.valid
    assert any(v["code"] == "ROOM_UNAVAILABLE" for v in res.violations)


def test_back_to_back_no_overlap():
    ctx = _ctx()
    # S1's two interviews are back-to-back (570 boundary) -> no overlap.
    ivs = [_iv("I1", "S1", start=540), _iv("I2", "S1", start=570)]
    res = validate(ivs, ctx)
    assert res.valid


def test_candidate_starts():
    starts = candidate_starts(540, 1020, 30)
    assert starts[0] == 540
    assert all(s % 5 == 0 for s in starts)
    # last valid start starts 30 min before the end.
    assert starts[-1] + 30 <= 1020


def test_day_grid():
    grid = day_time_grid(540, 1020)
    assert grid[0] == 540
    assert grid[-1] == 1015
