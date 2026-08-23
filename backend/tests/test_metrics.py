"""Tests for the metrics service."""
from __future__ import annotations

from app.services.metrics_service import compute_metrics

# (student, company, day, start, end, tier)
_STU = [
    ("S1", "C1", "DAY_1", 540, 570, "TIER_1"),
    ("S1", "C2", "DAY_1", 630, 660, "TIER_2"),
    ("S2", "C1", "DAY_1", 540, 570, "TIER_1"),
]


def test_coverage_and_counts():
    m = compute_metrics(_STU, total=4, room_available_minutes=2000, panel_available_minutes=10000)
    assert m.scheduled == 3
    assert m.unscheduled == 1
    assert m.coverage == 75.0


def test_utilization():
    m = compute_metrics(_STU, total=3, room_available_minutes=1000, panel_available_minutes=1000)
    # used = (570-540)+(660-630)+(570-540) = 30+30+30 = 90
    assert m.room_utilization == 9.0
    assert m.panel_utilization == 9.0


def test_average_waiting():
    m = compute_metrics([_STU[0], _STU[1]], total=2, room_available_minutes=1000, panel_available_minutes=1000)
    # S1: gap = 630 - 570 = 60
    assert m.avg_wait_minutes == 60.0


def test_replan_churn():
    m = compute_metrics(_STU, total=3, room_available_minutes=1000, panel_available_minutes=1000,
                        moved_count=5, previous_scheduled=100)
    assert m.replan_churn == 5.0


def test_by_day_and_tier():
    m = compute_metrics(_STU, total=3, room_available_minutes=1000, panel_available_minutes=1000)
    assert m.interviews_by_day == {"DAY_1": 3}
    assert m.interviews_by_tier == {"TIER_1": 2, "TIER_2": 1}
