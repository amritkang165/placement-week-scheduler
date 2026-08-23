"""Scheduling quality metrics.

Pure functions so they can be unit-tested without a database. The service layer
feeds them the current schedule and the available capacity.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Metrics:
    total: int = 0
    scheduled: int = 0
    unscheduled: int = 0
    coverage: float = 0.0
    student_clashes: int = 0
    room_utilization: float = 0.0
    panel_utilization: float = 0.0
    avg_wait_minutes: float = 0.0
    replan_churn: float = 0.0
    solver_status: str = "UNKNOWN"
    schedule_status: str = "UNKNOWN"
    interviews_by_day: dict = field(default_factory=dict)
    interviews_by_tier: dict = field(default_factory=dict)


# A scheduled interview as a plain tuple:
# (student_id, company_id, day, start_min, end_min, tier)
ScheduledEntry = tuple[str, str, str, int, int, str]


def compute_metrics(
    scheduled: list[ScheduledEntry],
    total: int,
    room_available_minutes: int,
    panel_available_minutes: int,
    solver_status: str = "UNKNOWN",
    schedule_status: str = "UNKNOWN",
    moved_count: int | None = None,
    previous_scheduled: int | None = None,
    student_clashes: int = 0,
) -> Metrics:
    m = Metrics()
    m.total = total
    m.scheduled = len(scheduled)
    m.unscheduled = total - len(scheduled)
    m.coverage = round(m.scheduled / total * 100, 2) if total else 0.0
    m.student_clashes = student_clashes
    m.solver_status = solver_status
    m.schedule_status = schedule_status

    used_room_min = sum(e[4] - e[3] for e in scheduled)
    m.room_utilization = round(used_room_min / room_available_minutes * 100, 2) if room_available_minutes else 0.0

    used_panel_min = sum(e[4] - e[3] for e in scheduled)
    m.panel_utilization = round(used_panel_min / panel_available_minutes * 100, 2) if panel_available_minutes else 0.0

    m.avg_wait_minutes = _average_waiting(scheduled)

    if moved_count is not None and previous_scheduled:
        m.replan_churn = round(moved_count / previous_scheduled * 100, 2)

    m.interviews_by_day = _count_by(scheduled, key=lambda e: e[2])
    m.interviews_by_tier = _count_by(scheduled, key=lambda e: e[5])
    return m


def _average_waiting(scheduled: list[ScheduledEntry]) -> float:
    by_student_day: dict[tuple[str, str], list[ScheduledEntry]] = {}
    for e in scheduled:
        by_student_day.setdefault((e[0], e[2]), []).append(e)

    waits: list[int] = []
    for items in by_student_day.values():
        items = sorted(items, key=lambda e: e[3])
        for i in range(len(items) - 1):
            gap = items[i + 1][3] - items[i][4]  # next.start - current.end
            if gap > 0:
                waits.append(gap)

    return round(sum(waits) / len(waits), 1) if waits else 0.0


def _count_by(scheduled: list[ScheduledEntry], key) -> dict:
    counts: dict[str, int] = {}
    for e in scheduled:
        k = key(e)
        counts[k] = counts.get(k, 0) + 1
    return counts


# A record used for conflict detection. Fields align with InterviewRecord:
#  - interview_id, student_id, company_id, day, start, end, room_id, panel_id
ConflictRecord = tuple[str, str, str, str, int, int, str, str]


def detect_conflicts(records: list[ConflictRecord]) -> list[dict]:
    """Return a list of human-readable conflict objects.

    Checks, for all scheduled interviews on the same day:
      * a student overlapping themselves (STUDENT_CLASH)
      * a room double-booked (ROOM_CLASH)
      * a panel double-booked (PANEL_CLASH)
    """
    conflicts: list[dict] = []
    cid = 0

    def _overlaps(a: ConflictRecord, b: ConflictRecord) -> bool:
        return a[3] == b[3] and a[4] < b[5] and b[4] < a[5]

    # Student clashes.
    by_student_day: dict[tuple[str, str], list[ConflictRecord]] = {}
    for r in records:
        by_student_day.setdefault((r[1], r[3]), []).append(r)
    for (_, _), items in by_student_day.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if _overlaps(items[i], items[j]):
                    cid += 1
                    conflicts.append(
                        {
                            "conflict_id": f"C-{cid:03d}",
                            "type": "STUDENT_CLASH",
                            "entity_id": items[i][1],
                            "message": (
                                f"Student {items[i][1]} is booked in two interviews at the same time "
                                f"({items[i][0]}, {items[j][0]}) on day {items[i][3]}."
                            ),
                            "interview_ids": [items[i][0], items[j][0]],
                            "involved": [
                                {"id": x[0], "room_id": x[6], "panel_id": x[7], "start": x[4], "end": x[5]}
                                for x in (items[i], items[j])
                            ],
                        }
                    )

    # Room clashes.
    by_room_day: dict[tuple[str, str], list[ConflictRecord]] = {}
    for r in records:
        by_room_day.setdefault((r[6], r[3]), []).append(r)
    for (_, _), items in by_room_day.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if _overlaps(items[i], items[j]):
                    cid += 1
                    conflicts.append(
                        {
                            "conflict_id": f"C-{cid:03d}",
                            "type": "ROOM_CLASH",
                            "entity_id": items[i][6],
                            "message": (
                                f"Room {items[i][6]} is double-booked on day {items[i][3]} "
                                f"({items[i][0]}, {items[j][0]})."
                            ),
                            "interview_ids": [items[i][0], items[j][0]],
                            "involved": [
                                {"id": x[0], "student_id": x[1], "start": x[4], "end": x[5]}
                                for x in (items[i], items[j])
                            ],
                        }
                    )

    # Panel clashes.
    by_panel_day: dict[tuple[str, str], list[ConflictRecord]] = {}
    for r in records:
        by_panel_day.setdefault((r[7], r[3]), []).append(r)
    for (_, _), items in by_panel_day.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if _overlaps(items[i], items[j]):
                    cid += 1
                    conflicts.append(
                        {
                            "conflict_id": f"C-{cid:03d}",
                            "type": "PANEL_CLASH",
                            "entity_id": items[i][7],
                            "message": (
                                f"Panel {items[i][7]} is double-booked on day {items[i][3]} "
                                f"({items[i][0]}, {items[j][0]})."
                            ),
                            "interview_ids": [items[i][0], items[j][0]],
                            "involved": [
                                {"id": x[0], "student_id": x[1], "start": x[4], "end": x[5]}
                                for x in (items[i], items[j])
                            ],
                        }
                    )

    return conflicts
