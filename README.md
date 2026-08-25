# Placement Week Scheduler

[![CI](https://github.com/amritkang165/placement-week-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/amritkang165/placement-week-scheduler/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-4B8BBE)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)](#)
[![License](https://img.shields.io/badge/license-MIT-2ea044)](#)

A CP-SAT constraint scheduler and disruption-aware replanner for college placement week. It replaces the coordinator's whiteboard — the thing that "collapses daily" — with a system that builds a feasible schedule in seconds, survives the chaos on the day, and reports exactly what changed and who needs to be told.

Built for the **Mirai Labs · Assignment A** assessment: **35 companies, 800 students, 20 rooms, 4 days, 1,123 shortlists**.

---

## Highlights

- **Feasibility-first CP-SAT solver.** Never fails silently. When a perfect schedule is impossible, it says which interviews couldn't be placed and why.
- **Disruption-aware replanning.** Company arrives late, panel drops out, room goes dark, a student withdraws — all handled with minimal upheaval.
- **Transparent diff.** Every appointment is classified `UNCHANGED / MOVED / ADDED / CANCELLED`, with counts of students, rooms, and panels affected plus replan churn.
- **Coordinator dashboard.** Live state, conflict detection, and one-click replan with a change summary. Built for someone making decisions under pressure.
- **Bring your own data.** Manual forms, JSON import, or CSV upload.

**Result on the reference dataset (seed 42):**
`1117 / 1123` interviews scheduled (**99.5% coverage**), **0 student clashes**, **90% room utilization**, solved in seconds. Replan churn after a 2-hour company delay: **1.4%** (see [Metrics](#metrics)).

---

## Tech stack

| Layer | Stack |
|---|---|
| Solver | Google OR-Tools **CP-SAT** |
| Backend | **FastAPI** · SQLAlchemy · Pydantic · Alembic |
| Frontend | **React** · Vite · TypeScript · Tailwind · Recharts |
| Storage | PostgreSQL (SQLite for local dev & tests) |
| CI | GitHub Actions — backend tests + frontend build |

---

## Quick start

```bash
./start.sh --seed
```

Installs dependencies, generates the dataset, solves the initial schedule, and starts the backend (`:8000`) and frontend (`:5173`). Open **http://localhost:5173** — the board is pre-loaded.

> SQLite via `backend/.env` — **no database, Docker, or environment variables required**.

Manual run:

```bash
# Terminal 1 — API
cd backend && python3.11 -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend && npm install && npm run dev
```

Docker: `docker compose up --build` · Tests: `cd backend && python3.11 -m pytest -q`

---

## How it works

1. **Model.** One optional interval per interview per allowed day; `AddNoOverlap` per student; `AddCumulative` for room×day and panel×company×day; 30-minute slots from 09:00–17:00.
2. **Objective** (in priority order):
   - `scheduled_interview = 10000` → maximize coverage
   - tier bonus `{TIER_1: 300, TIER_2: 200, TIER_3: 100}` → favour Tier-1 mass recruiters
   - `earliness_minute = 1` → pack interviews early, cut waiting
   - `moved_interview = 5000`, `moved_minute = 5` → replan-only churn penalties
3. **Coloring.** Rooms and panels are assigned by a deterministic greedy interval coloring (start-time order, preferring the original resource on replans). The model stays small while guaranteeing no double-booking.
4. **Validate.** Every solution is re-checked by a pure validator before it is persisted. It reports `VALID`, or `PARTIAL`/`INFEASIBLE` with the reason per interview.

### Replanning under disruption

Replanning is **validity-based**: an appointment that is still legal in the new problem is **frozen** (day + start time) and never moves. Only the affected region is re-solved. Resources are re-colored freely, because time — not the room — is what the student actually depends on.

The **diff engine** then classifies every appointment and emits an impact summary: students / rooms / panels affected, and churn percentage.

---

## Project structure

```
├── backend/
│   ├── app/
│   │   ├── generator/   deterministic realistic dataset generator
│   │   ├── scheduler/   model, constraints, objective, CP-SAT solver, validator
│   │   ├── services/    scheduling, replanning, metrics, diff engine
│   │   ├── schemas/     Pydantic API contract
│   │   ├── api/         FastAPI routers
│   │   └── models/      SQLAlchemy ORM models
│   ├── alembic/         migrations
│   └── tests/           pytest suite
├── frontend/
│   └── src/
│       ├── lib/         typed API client, types, theme
│       ├── pages/       Board, Schedule, Disruptions, Analytics, Entities, Add Data
│       └── components/  StatCard, ConflictsWidget, UI primitives
├── scripts/             seed + demo scenarios
├── start.sh             one-command launcher
└── docker-compose.yml
```

---

## Metrics

| Metric | Definition |
|---|---|
| Coverage | % of shortlists scheduled. |
| Student clashes | A student double-booked — must be `0` in a VALID schedule. |
| Room / panel utilization | Hours booked ÷ hours available. |
| Avg student wait | Mean gap between consecutive interviews for a student. |
| Replan churn | Moved bookings ÷ previously scheduled. |

Because coverage is dominant, an interview that genuinely cannot be placed is left `UNSCHEDULED` **with a reason** rather than silently dropped. Soft preferences (earliness, ordering) bend first; the hard constraints (no overlap, no double-booking) never do. The coordinator drives the trade-off via the churn penalty and the pre/post diff — the system is transparent, not authoritative.

### Measured behaviour (seed 42)

| Disruption | Affected | Moved | Cancelled | Added | Churn |
|---|---|---|---|---|---|
| Company delayed 2h | 33 | 16 | 16 | 1 | 1.43% |
| Panel unavailable | 35 | 12 | 7 | 16 | 1.09% |
| Room unavailable | 61 | 34 | 21 | 6 | 3.06% |
| Student withdrew | 14 | 0 | 13 | 1 | 0.00% |

---

## Data & API

Add companies, students, rooms, panels, and shortlists from the **Add Data** page or via:

- `POST /api/data/{company|student|room|panel|shortlist}` — manual
- `POST /api/data/import` — bulk JSON · `POST /api/data/import/csv` — bulk CSV
- `DELETE /api/data/all` — reset

Full REST surface (docs at **`/docs`** on the running API):

```
POST /api/generate-data            generate dataset
POST /api/schedule                 solve & persist
GET  /api/schedule                 active version + interviews
GET  /api/schedule/versions        list versions
GET  /api/schedule/metrics         quality metrics
GET  /api/schedule/conflicts       double-bookings
GET  /api/schedule/{id}/changes    diff vs previous version
POST /api/disruptions              record a disruption
POST /api/replan                   re-solve around disruptions
POST /api/data/...                 add / import / wipe data
```

Valid placement days are `DAY_1`–`DAY_4`, fixed to 2026-08-24 → 08-27.

---

## Tests

```bash
cd backend && python3.11 -m pytest -q     # 45 tests
```

Covers constraints, validator, metrics, the diff engine, the API, and the replanner for all four disruption types (SQLite, low solver time limit).

---

## License

[MIT](./LICENSE) © 2026 Amrit Kang
