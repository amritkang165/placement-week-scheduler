"""Shared time / placement-day constants and helpers.

Times are represented internally as minutes-since-midnight integers; the API
and database layers convert to/from "HH:MM" strings.
"""
from __future__ import annotations

import datetime as _dt

# Placement day keys and their concrete calendar dates.
DAY_KEYS: tuple[str, ...] = ("DAY_1", "DAY_2", "DAY_3", "DAY_4")
DAY_DATES: dict[str, str] = {
    "DAY_1": "2026-08-24",
    "DAY_2": "2026-08-25",
    "DAY_3": "2026-08-26",
    "DAY_4": "2026-08-27",
}
DAY_INDEX: dict[str, int] = {k: i for i, k in enumerate(DAY_KEYS)}

# Default operating hours.
OPERATING_START_MIN = 9 * 60   # 09:00
OPERATING_END_MIN = 17 * 60    # 17:00

# Slot granularity (minutes). Divides 20/30/45/60-min durations.
SLOT_STEP_MIN = 5

# Valid interview durations.
DURATIONS: tuple[int, ...] = (20, 30, 45, 60)

# Branches.
BRANCHES: tuple[str, ...] = ("CSE", "ISE", "ECE", "EEE", "ME", "CIVIL")

TIERS: tuple[str, ...] = ("TIER_1", "TIER_2", "TIER_3")


def minutes_to_time_str(minutes: int) -> str:
    """Convert minutes-since-midnight to an 'HH:MM' string."""
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


def time_str_to_minutes(value: str) -> int:
    """Convert an 'HH:MM' (or 'HH:MM:SS') string to minutes-since-midnight."""
    parts = value.strip().split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return hours * 60 + minutes


def date_to_day_key(date_str: str) -> str:
    for key, d in DAY_DATES.items():
        if d == date_str:
            return key
    raise ValueError(f"Unknown placement date: {date_str}")


def day_key_to_date(day_key: str) -> str:
    return DAY_DATES[day_key]


def time_between(start_min: int, end_min: int) -> int:
    """Minutes between two times; always non-negative (no overnight wrap)."""
    return max(0, end_min - start_min)


def parse_datetime(dt: _dt.datetime | str) -> _dt.datetime:
    if isinstance(dt, _dt.datetime):
        return dt
    return _dt.datetime.fromisoformat(dt)
