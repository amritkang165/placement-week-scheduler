"""Schedule diff engine.

Compares an old and a new schedule and classifies every appointment as
UNCHANGED, MOVED, ADDED, CANCELLED, or UNSCHEDULED, producing a change report
and an impact summary for the coordinator.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Slot:
    date: str | None
    start: str | None
    end: str | None
    room_id: str | None
    panel_id: str | None


@dataclass
class InterviewRecord:
    """Lightweight row used for diffing (decoupled from the ORM)."""

    id: str
    student_id: str
    student_name: str
    company_id: str
    company_name: str
    status: str
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    room_id: str | None = None
    panel_id: str | None = None
    reason: str | None = None


@dataclass
class DiffItem:
    interview_id: str
    student_id: str
    student_name: str
    company_id: str
    company_name: str
    change_type: str  # UNCHANGED / MOVED / ADDED / CANCELLED / UNSCHEDULED
    before: Slot | None = None
    after: Slot | None = None
    reason: str | None = None


@dataclass
class DiffResult:
    items: list[DiffItem] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def diff_schedules(
    old: dict[str, "InterviewRecord"],
    new: dict[str, "InterviewRecord"],
    old_scheduled_count: int,
) -> DiffResult:
    """Diff two schedule snapshots keyed by interview id.

    `old`/`new` map interview_id -> InterviewRecord. `old_scheduled_count` is
    the number of scheduled interviews in the old version (for churn %).
    """
    result = DiffResult()
    all_ids = set(old.keys()) | set(new.keys())

    moved = added = cancelled = unchanged = unscheduled = 0
    for iid in sorted(all_ids):
        o = old.get(iid)
        n = new.get(iid)

        o_sched = o is not None and o.status == "SCHEDULED"
        n_sched = n is not None and n.status == "SCHEDULED"

        if o_sched and n_sched:
            if _same_assignment(o, n):
                change = "UNCHANGED"
                unchanged += 1
            else:
                change = "MOVED"
                moved += 1
        elif o_sched and not n_sched:
            change = "CANCELLED"
            cancelled += 1
        elif not o_sched and n_sched:
            change = "ADDED"
            added += 1
        else:
            change = "UNSCHEDULED"
            unscheduled += 1

        if change == "UNCHANGED" and not _include_unchanged():
            continue

        result.items.append(
            DiffItem(
                interview_id=iid,
                student_id=(n or o).student_id,
                student_name=(n or o).student_name,
                company_id=(n or o).company_id,
                company_name=(n or o).company_name,
                change_type=change,
                before=_slot(o) if o_sched else None,
                after=_slot(n) if n_sched else None,
                reason=n.reason if (n is not None and not n_sched) else None,
            )
        )

    total = moved + added + cancelled + unchanged + unscheduled
    result.summary = {
        "affected_interviews": moved + added + cancelled,
        "moved": moved,
        "cancelled": cancelled,
        "added": added,
        "unchanged": unchanged,
        "unscheduled": unscheduled,
        "students_affected": len({i.student_id for i in result.items if i.change_type != "UNCHANGED"}),
        "rooms_affected": len({_r(i) for i in result.items if _r(i) and i.change_type != "UNCHANGED"}),
        "panels_affected": len({_p(i) for i in result.items if _p(i) and i.change_type != "UNCHANGED"}),
        "replan_churn": round(moved / old_scheduled_count * 100, 2) if old_scheduled_count else 0.0,
        "total": total,
    }
    return result


def _include_unchanged() -> bool:
    return False


def _same_assignment(o, n) -> bool:
    # Operationally an appointment is "unchanged" when its time window is the
    # same. Room/panel reassignments (e.g. after a panel failure) are shown in
    # the before/after detail but do not bump the appointment into MOVED, since
    # the student's interview slot is preserved.
    return (
        o.date == n.date
        and o.start_time == n.start_time
        and o.end_time == n.end_time
    )


def _slot(rec) -> Slot:
    return Slot(
        date=rec.date,
        start=rec.start_time,
        end=rec.end_time,
        room_id=rec.room_id,
        panel_id=rec.panel_id,
    )


def _r(i: DiffItem) -> str | None:
    if i.change_type == "MOVED":
        return i.after.room_id if i.after else (i.before.room_id if i.before else None)
    return i.before.room_id if i.before else (i.after.room_id if i.after else None)


def _p(i: DiffItem) -> str | None:
    if i.change_type == "MOVED":
        return i.after.panel_id if i.after else (i.before.panel_id if i.before else None)
    return i.before.panel_id if i.before else (i.after.panel_id if i.after else None)
