from app.services.metrics_service import detect_conflicts


# record = (id, student_id, company_id, day, start, end, room_id, panel_id)
def test_student_clash_detected():
    recs = [
        ("I1", "S1", "C1", "D1", 540, 600, "R1", "P1"),
        ("I2", "S1", "C2", "D1", 570, 630, "R2", "P2"),
    ]
    conflicts = detect_conflicts(recs)
    types = [c["type"] for c in conflicts]
    assert "STUDENT_CLASH" in types
    assert len([c for c in conflicts if c["type"] == "STUDENT_CLASH"]) == 1


def test_room_clash_detected():
    recs = [
        ("I1", "S1", "C1", "D1", 540, 600, "R1", "P1"),
        ("I2", "S2", "C2", "D1", 570, 630, "R1", "P2"),
    ]
    conflicts = detect_conflicts(recs)
    assert any(c["type"] == "ROOM_CLASH" for c in conflicts)


def test_no_conflict_for_sequential():
    recs = [
        ("I1", "S1", "C1", "D1", 540, 600, "R1", "P1"),
        ("I2", "S1", "C2", "D1", 600, 660, "R1", "P1"),
    ]
    assert detect_conflicts(recs) == []


def test_non_overlapping_rooms_no_clash():
    recs = [
        ("I1", "S1", "C1", "D1", 540, 600, "R1", "P1"),
        ("I2", "S1", "C2", "D1", 600, 660, "R2", "P2"),
    ]
    assert detect_conflicts(recs) == []
