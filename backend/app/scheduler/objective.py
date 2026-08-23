"""Objective function definition.

The CP-SAT model maximizes a single linear score:

    score = SUM_i scheduled_i * W.scheduled_interview          (coverage)
          + SUM_i scheduled_i * W.priority[tier_i]            (priority)
          - SUM_i active_start_i * W.earliness_minute         (packing/waiting)
          - SUM_i moved_i * W.moved_interview                 (replan churn)
          - SUM_i moved_minutes_i * W.moved_minute            (replan shift)

Reasoning for the weights (all configurable, see config.SolverWeights):

* scheduled_interview (10000) dominates so coverage is always the top goal.
  A move (5000 + 5/min) is always preferred to dropping (which loses 10000),
  but among feasible placements the one closest to the original is chosen.
* priority (300/200/100) makes higher-tier interviews slightly preferable when
  a choice exists, but never at the cost of a hard constraint or coverage.
* earliness (1/min) packs interviews toward the start of the day. Packing
  minimizes idle gaps and therefore average student waiting time, while the
  10x margin to coverage guarantees a late slot is never dropped.
* moved_interview (5000) / moved_minute (5/min) apply during replanning and
  discourage unnecessary churn, while still allowing a move when required.

Move terms only apply to interviews that are actually scheduled (scheduled_i=1)
and are NOT frozen. Frozen interviews are fixed and cannot be moved.
"""
from __future__ import annotations

from ortools.sat.python import cp_model

from app.config import SolverWeights
from app.scheduler.types import InterviewRequirement, ProblemInput

DAY_LENGTH = 24 * 60  # minutes offset between consecutive placement days


class InterviewVars:
    """All CP-SAT variables associated with a single interview requirement."""

    def __init__(self) -> None:
        self.day_presence: dict[str, cp_model.IntVar] = {}
        self.day_start: dict[str, cp_model.IntVar] = {}
        self.day_interval = {}  # day -> IntervalVar
        self.scheduled: cp_model.IntVar | None = None
        self.active_start: cp_model.IntVar | None = None
        self.abs_start: cp_model.IntVar | None = None
        # Replanning-only auxiliary variables.
        self.moved: cp_model.IntVar | None = None
        self.moved_minutes: cp_model.IntVar | None = None


def build_objective(
    model: cp_model.CpModel,
    problem: ProblemInput,
    weights: SolverWeights,
    var_bundles: dict[str, InterviewVars],
) -> None:
    """Construct the maximize expression and attach it to the model."""
    req_by_id: dict[str, InterviewRequirement] = {r.id: r for r in problem.interviews}
    day_offset = {day: idx * DAY_LENGTH for idx, day in enumerate(_day_keys(problem))}

    terms: list[tuple[cp_model.LinearExpr, int]] = []

    for req in problem.interviews:
        v = var_bundles[req.id]
        assert v.scheduled is not None
        assert v.active_start is not None
        assert v.abs_start is not None

        # Coverage + priority.
        terms.append((v.scheduled, weights.scheduled_interview))
        terms.append((v.scheduled, weights.priority.get(req.tier, 0)))

        # Earliness / packing (minimize waiting).
        terms.append((v.active_start, -weights.earliness_minute))

        # Replanning move penalty (skip frozen / new interviews).
        original = problem.original.get(req.id)
        if original is not None and req.id not in problem.frozen:
            _add_move_terms(
                model,
                problem,
                req,
                v,
                original,
                weights,
                day_offset,
                terms,
            )

    # Minimizing X is equivalent to maximizing -X.
    objective = None
    for expr, coeff in terms:
        term = expr * coeff
        objective = term if objective is None else objective + term
    model.Maximize(objective)


def _add_move_terms(
    model: cp_model.CpModel,
    problem: ProblemInput,
    req: InterviewRequirement,
    v: InterviewVars,
    original,
    weights: SolverWeights,
    day_offset: dict[str, int],
    terms: list,
) -> None:
    """Add |new_start - old_start| and moved(0/1) terms for replanning."""
    orig_abs = day_offset[original.day] + original.start

    # abs_start == original -> not moved.
    eq = model.NewBoolVar(f"moved_{req.id}_eq")
    model.Add(v.abs_start == orig_abs).OnlyEnforceIf(eq)
    model.Add(v.abs_start != orig_abs).OnlyEnforceIf(eq.Not())

    # moved = scheduled AND (abs_start != original).
    v.moved = model.NewBoolVar(f"moved_{req.id}")
    model.Add(v.scheduled == 1).OnlyEnforceIf(v.moved)
    model.Add(v.abs_start != orig_abs).OnlyEnforceIf(v.moved)

    # moved_minutes = |abs_start - original|, but only counted when scheduled.
    delta = model.NewIntVar(-4 * DAY_LENGTH, 4 * DAY_LENGTH, f"delta_{req.id}")
    model.Add(delta == v.abs_start - orig_abs)
    abs_delta = model.NewIntVar(0, 4 * DAY_LENGTH, f"absdelta_{req.id}")
    model.AddAbsEquality(abs_delta, delta)
    v.moved_minutes = model.NewIntVar(0, 4 * DAY_LENGTH, f"movemin_{req.id}")
    model.AddMultiplicationEquality(v.moved_minutes, [abs_delta, v.scheduled])

    terms.append((v.moved, -weights.moved_interview))
    terms.append((v.moved_minutes, -weights.moved_minute))


def _day_keys(problem: ProblemInput) -> list[str]:
    keys = set()
    for c in problem.companies.values():
        keys.update(c.windows.keys())
    if not keys:
        # Fall back to all rooms' available days.
        for r in problem.rooms.values():
            keys.update(r.available_days)
    return sorted(keys)
