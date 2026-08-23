"""Tests for the deterministic data generator."""
from __future__ import annotations

from app.generator.placement_data import generate_data
from app.scheduler.time_utils import BRANCHES, DURATIONS, TIERS


def test_counts():
    data = generate_data(seed=42)
    assert len(data.companies) == 35
    assert len(data.students) == 800
    assert len(data.rooms) == 20
    assert len(data.panels) > 0
    assert len(data.shortlists) > 800  # realistic overlap exists


def test_deterministic():
    a = generate_data(seed=42)
    b = generate_data(seed=42)
    c = generate_data(seed=7)
    assert a.shortlists[0].id == b.shortlists[0].id
    assert a.students[0].name == b.students[0].name
    # Different seed -> different data.
    assert not all(x.name == y.name for x, y in zip(a.students, c.students))


def test_valid_cgpa_and_branch():
    data = generate_data(seed=42)
    for s in data.students:
        assert 6.0 <= s.cgpa <= 10.0
        assert s.branch in BRANCHES
        assert s.year in (3, 4) and s.year >= 2


def test_company_configuration():
    data = generate_data(seed=42)
    tiers = {c.priority_tier for c in data.companies}
    assert tiers <= set(TIERS)
    assert len(tiers) == 3  # all three tiers present
    for c in data.companies:
        assert c.interview_duration_minutes in DURATIONS
        assert c.panel_count >= 1
        assert 6.0 <= c.cgpa_cutoff <= 9.0
        assert len(c.available_days) >= 1
        assert len(c.availability_windows) == len(c.available_days)


def test_rooms_only_20():
    data = generate_data(seed=42)
    ids = {r.id for r in data.rooms}
    assert ids == {f"ROOM-{i:02d}" for i in range(1, 21)}


def test_top_students_shortlisted_more():
    data = generate_data(seed=42)
    counts = {s.id: 0 for s in data.students}
    for sl in data.shortlists:
        counts[sl.student_id] += 1
    cgpa = {s.id: s.cgpa for s in data.students}
    top = [s.id for s in data.students if s.cgpa >= 9.0]
    low = [s.id for s in data.students if s.cgpa <= 7.0]
    avg_top = sum(counts[s] for s in top) / max(1, len(top))
    avg_low = sum(counts[s] for s in low) / max(1, len(low))
    assert avg_top > avg_low  # top students appear on more shortlists


def test_shortlist_respects_cutoff():
    data = generate_data(seed=42)
    cutoff = {c.id: c.cgpa_cutoff for c in data.companies}
    cgpa = {s.id: s.cgpa for s in data.students}
    for sl in data.shortlists:
        assert cgpa[sl.student_id] >= cutoff[sl.company_id]
