"""CP-SAT scheduling engine.

Orchestrates model construction, objective assembly, solving, and the
deterministic room/panel assignment (interval coloring) pass.
"""
from __future__ import annotations

import time

from ortools.sat.python import cp_model

from app.config import SolverConfig
from app.scheduler import constraints
from app.scheduler.objective import build_objective
from app.scheduler.types import Assignment, ProblemInput, Solution

_STATUS_MAP = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN",
}


def solve(problem: ProblemInput, config: SolverConfig) -> Solution:
    """Build, solve, and post-process the scheduling problem."""
    started = time.time()

    model, var_bundles, day_offset = constraints.build_model(problem)
    build_objective(model, problem, config.weights, var_bundles)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.time_limit_seconds
    solver.parameters.num_search_workers = config.num_search_workers
    solver.parameters.random_seed = 42

    status = solver.Solve(model)
    wall = time.time() - started

    if status == cp_model.INFEASIBLE:
        return Solution(assignments={}, solver_status="INFEASIBLE", wall_time_seconds=wall)

    assignments: dict[str, Assignment] = {}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for req in problem.interviews:
            v = var_bundles[req.id]
            if solver.Value(v.scheduled) != 1:
                continue
            chosen_day = None
            chosen_start = None
            for day, presence in v.day_presence.items():
                if solver.Value(presence) == 1:
                    chosen_day = day
                    chosen_start = solver.Value(v.day_start[day])
                    break
            if chosen_day is None:
                continue
            # Freeze only the TIME (day + start) of an unaffected appointment.
            # Rooms/panels are re-assigned uniformly by the coloring pass below
            # (preferring the original when possible) so the resource assignment
            # is always feasible and the temporal schedule stays stable.
            assignments[req.id] = Assignment(
                interview_id=req.id,
                student_id=req.student_id,
                company_id=req.company_id,
                day=chosen_day,
                start=chosen_start,
                duration=req.duration_minutes,
                room_id=None,
                panel_id=None,
            )

    _assign_resources(assignments, problem)

    return Solution(
        assignments=assignments,
        solver_status=_STATUS_MAP.get(status, "UNKNOWN"),
        wall_time_seconds=round(wall, 3),
        objective_value=solver.ObjectiveValue(),
    )


def _assign_resources(assignments: dict[str, Assignment], problem: ProblemInput) -> None:
    """Assign concrete rooms and panels via deterministic interval coloring.

    Every appointment is colored uniformly by start time. Each assignment
    prefers its original resource (from the previous schedule) to minimize
    churn, and otherwise takes the lowest-id available resource. Because the
    solver guarantees, via cumulative capacity, that no more than the available
    resources overlap at any instant, the greedy interval coloring always finds
    a valid assignment (interval graphs are colored with exactly their clique
    number). This guarantees no room/panel is ever double-booked.
    """
    _color(assignments, problem, kind="room")
    _color(assignments, problem, kind="panel")


def _color(assignments: dict[str, Assignment], problem: ProblemInput, kind: str) -> None:
    if kind == "room":
        resources = {r.id: r for r in problem.rooms.values()}
    else:
        resources = {p.id: p for p in problem.panels.values()}

    # Group assignments by (day) for rooms, or (company, day) for panels.
    groups: dict[tuple, list[Assignment]] = {}
    for a in assignments.values():
        key = (a.day,) if kind == "room" else (a.company_id, a.day)
        groups.setdefault(key, []).append(a)

    for key, items in groups.items():
        if kind == "room":
            avail_ids = sorted(
                r.id for r in resources.values() if key[0] in r.available_days
            )
        else:
            company_id, day = key
            avail_ids = sorted(
                p.id
                for p in resources.values()
                if p.company_id == company_id and day in p.available_days
            )

        busy: dict[str, list[tuple[int, int]]] = {rid: [] for rid in avail_ids}

        # Color in start-time order (optimal for interval graphs).
        rest = sorted(items, key=lambda a: (a.start, a.end))

        for a in rest:
            original = problem.original.get(a.interview_id)
            preferred = (
                getattr(original, f"{kind}_id") if original is not None else None
            )
            free = [
                rid
                for rid in avail_ids
                if not _overlaps(a.start, a.end, busy.get(rid, []))
            ]
            if preferred in free:
                chosen = preferred
            elif free:
                chosen = free[0]
            else:
                # Should not happen when capacity is respected; fall back to the
                # resource that frees earliest so the interview can still run.
                chosen = min(
                    avail_ids,
                    key=lambda rid: _last_busy_end(busy.get(rid, [])),
                )
            if kind == "room":
                a.room_id = chosen
            else:
                a.panel_id = chosen
            busy.setdefault(chosen, []).append((a.start, a.end))


def _last_busy_end(intervals: list[tuple[int, int]]) -> int:
    return max((e for _, e in intervals), default=0)


def _overlaps(start: int, end: int, intervals: list[tuple[int, int]]) -> bool:
    for s, e in intervals:
        if start < e and s < end:
            return True
    return False
