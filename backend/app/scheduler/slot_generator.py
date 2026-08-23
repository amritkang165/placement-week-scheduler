"""Candidate time-slot generation.

Produces the discrete start-time grid used by the CP-SAT model and by the
frontend timeline. Interview durations must be a multiple of SLOT_STEP_MIN.
"""
from __future__ import annotations

from app.scheduler.time_utils import SLOT_STEP_MIN


def candidate_starts(
    window_start: int, window_end: int, duration: int, step: int = SLOT_STEP_MIN
) -> list[int]:
    """All valid start minutes for an interview of `duration` inside a window."""
    starts: list[int] = []
    t = window_start
    while t + duration <= window_end:
        starts.append(t)
        t += step
    return starts


def day_time_grid(
    window_start: int, window_end: int, step: int = SLOT_STEP_MIN
) -> list[int]:
    """All time boundaries (start of each slot) for a day."""
    return list(range(window_start, window_end, step))
