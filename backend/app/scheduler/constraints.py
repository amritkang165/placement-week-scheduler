"""Hard-constraint construction for the CP-SAT model.

Hard constraints are modeled as solver constraints that can never be violated:

* H1 Student no-overlap      -> AddNoOverlap per student
* H2 Room capacity           -> AddCumulative per day (rooms as capacity resource)
* H3 Panel capacity          -> AddCumulative per company per day
* H4 Company availability    -> start domain restricted to company windows
* H5 Panel availability      -> panel capacity accounts for available panels/day
* H6 Room availability       -> room capacity accounts for available rooms/day
* H7 CGPA eligibility        -> candidates filtered before modeling (validated after)
* H8 Student withdrawal      -> candidates filtered before modeling (validated after)
* H9 Company delay           -> window start shifted for the delayed day

Rooms and panels are non-overlapping resources. Because rooms (and a company's
panels) are interchangeable, they are modeled as *capacity* resources with a
per-day count; the concrete room/panel for each interview is chosen by a
deterministic coloring pass (see solver.assign_resources) and re-validated by
the validator. This keeps the model compact while still guaranteeing that no
room or panel is ever double-booked.
"""
from __future__ import annotations

from ortools.sat.python import cp_model

from app.scheduler.objective import DAY_LENGTH, InterviewVars
from app.scheduler.types import ProblemInput, problem_days


def build_model(
    problem: ProblemInput,
) -> tuple[cp_model.CpModel, dict[str, InterviewVars], dict[str, int]]:
    model = cp_model.CpModel()
    days = problem_days(problem)
    day_offset = {day: idx * DAY_LENGTH for idx, day in enumerate(days)}

    # Company -> {panel_id} lookup, company -> list of its interview ids.
    panel_company = {p.id: p.company_id for p in problem.panels.values()}
    company_interviews: dict[str, list[str]] = {}
    for req in problem.interviews:
        company_interviews.setdefault(req.company_id, []).append(req.id)

    var_bundles: dict[str, InterviewVars] = {}
    intervals_by_day: dict[str, list] = {d: [] for d in days}
    intervals_by_company_day: dict[tuple[str, str], list] = {}

    frozen_by_id = problem.frozen

    for req in problem.interviews:
        company = problem.companies[req.company_id]
        v = InterviewVars()
        var_bundles[req.id] = v

        frozen = frozen_by_id.get(req.id)
        allowed_days = [d for d in days if d in company.windows]

        for day in allowed_days:
            win_start, win_end = company.windows[day]
            start_domain = _start_domain(win_start, win_end, req.duration_minutes)
            presence = model.NewBoolVar(f"p_{req.id}_{day}")
            start = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(start_domain), f"s_{req.id}_{day}"
            )
            interval = model.NewOptionalIntervalVar(
                start,
                req.duration_minutes,
                start + req.duration_minutes,
                presence,
                f"iv_{req.id}_{day}",
            )
            v.day_presence[day] = presence
            v.day_start[day] = start
            v.day_interval[day] = interval
            intervals_by_day[day].append(interval)
            intervals_by_company_day.setdefault((req.company_id, day), []).append(interval)

        # At most one day per interview (H4: only company's available days).
        if len(allowed_days) > 1:
            model.AddAtMostOne(list(v.day_presence.values()))

        # scheduled == sum of day presence.
        v.scheduled = model.NewBoolVar(f"sched_{req.id}")
        model.Add(v.scheduled == cp_model.LinearExpr.Sum(list(v.day_presence.values())))

        # active_start = start of the chosen day (0 if unscheduled).
        v.active_start = model.NewIntVar(
            0, 24 * 60, f"active_start_{req.id}"
        )
        active_terms = []
        for day, start in v.day_start.items():
            prod = model.NewIntVar(0, 24 * 60, f"as_{req.id}_{day}")
            model.AddMultiplicationEquality(prod, [start, v.day_presence[day]])
            active_terms.append(prod)
        model.Add(v.active_start == cp_model.LinearExpr.Sum(active_terms))

        # abs_start = day offset + active_start.
        v.abs_start = model.NewIntVar(0, 4 * DAY_LENGTH, f"abs_{req.id}")
        day_term = cp_model.LinearExpr.Sum(
            [v.day_presence[d] * day_offset[d] for d in allowed_days]
        )
        model.Add(v.abs_start == day_term + v.active_start)

        # Freeze unaffected appointments: pin day, start, and presence.
        if frozen is not None:
            model.Add(v.scheduled == 1)
            for day in allowed_days:
                if day == frozen.day:
                    model.Add(v.day_presence[day] == 1)
                    model.Add(v.day_start[day] == frozen.start)
                else:
                    model.Add(v.day_presence[day] == 0)

    # H1: student no-overlap.
    student_interviews: dict[str, list] = {}
    for req in problem.interviews:
        student_interviews.setdefault(req.student_id, []).append(req.id)
    for sid, ids in student_interviews.items():
        if len(ids) < 2:
            continue
        model.AddNoOverlap(
            [iv for i in ids for iv in var_bundles[i].day_interval.values()]
        )

    # H2: room capacity per day (rooms available that day).
    for day in days:
        room_cap = sum(1 for r in problem.rooms.values() if day in r.available_days)
        if room_cap <= 0:
            # No room available -> force all interviews off this day.
            for req in problem.interviews:
                v = var_bundles[req.id]
                if day in v.day_presence:
                    model.Add(v.day_presence[day] == 0)
            continue
        model.AddCumulative(intervals_by_day[day], [1] * len(intervals_by_day[day]), room_cap)

    # H3: panel capacity per company per day (panels available that day).
    for (company_id, day), ivs in intervals_by_company_day.items():
        panel_cap = sum(
            1
            for p in problem.panels.values()
            if p.company_id == company_id and day in p.available_days
        )
        if panel_cap <= 0:
            # This company has no panel on this day -> force those interviews off.
            for req_id in company_interviews.get(company_id, []):
                v = var_bundles[req_id]
                if day in v.day_presence:
                    model.Add(v.day_presence[day] == 0)
            continue
        model.AddCumulative(ivs, [1] * len(ivs), panel_cap)

    return model, var_bundles, day_offset


def _start_domain(win_start: int, win_end: int, duration: int) -> list[int]:
    from app.scheduler.slot_generator import candidate_starts

    return candidate_starts(win_start, win_end, duration)
