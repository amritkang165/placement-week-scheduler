# Placement Week Scheduler

![CI](https://github.com/amritkang165/placement-week-scheduler/actions/workflows/ci.yml/badge.svg)
![Python 3.11](https://img.shields.io/badge/Python-3.11-4B8BBE)
![Node 20](https://img.shields.io/badge/Node-20-3C873A)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![License](https://img.shields.io/badge/License-MIT-blue)

A **CP-SAT–powered scheduler and disruption-aware replanner** for placement week.
It replaces the coordinator's whiteboard — which "collapses daily" — with a
system that produces a feasible schedule in seconds, survives the chaos of the
day, and tells you exactly what changed and who needs to be told.

> Built for the **Mirai Labs · Assignment A** technical assessment: 35 companies,
> 800 students, 20 interview rooms, 4 days, and 1,123 shortlists.

---

## Features

- **Deterministic, realistic dataset generator** — mass-recruiting Tier-1
  companies, overlapping shortlists, CGPA cutoffs, panels, and per-day availability.
- **Feasibility-first CP-SAT solver** — never fails silently. When a perfect
  schedule is impossible it says exactly what couldn't be scheduled and why.
- **Disruption-aware replanner** — handles a company arriving late, a panel
  dropping out, a room going dark, and a student withdrawing — while disturbing
  the existing schedule as little as possible.
- **Transparent diff + impact summary** — every appointment is classified
  `UNCHANGED / MOVED / ADDED / CANCELLED`, with students/rooms/panels affected
  and replan churn %.
- **Coordinator dashboard** — current state, conflicts, one-click replan, and a
  change summary built for people making decisions in real time.
- **Bring your own data** — manual forms, JSON import, or CSV upload for real
  placement data.
- **Editorial UI** — dark mode, serif headlines, and a "coordinators' board"
  aesthetic.

---

## Tech stack

| Layer | Tech |
|---|---|
| Solver | Google **OR-Tools CP-SAT** (`ortools`) |
| Backend | **FastAPI** · SQLAlchemy · Pydantic · Alembic |
| Frontend | **React** · Vite · TypeScript · Tailwind + Recharts |
| Storage | PostgreSQL (SQLite for local dev / tests) |
| CI | GitHub Actions (backend tests + frontend build) |

---

## Architecture

```
placement-week-scheduler/
├── backend/
│   ├── app/
│   │   ├── generator/     deterministic realistic dataset generator
│   │   ├── scheduler/     problem model, constraints, objective, CP-SAT solver, validator
│   │   ├── services/      scheduling, replanning, metrics, diff engine (pure functions)
│   │   ├── schemas/       Pydantic API contract
│   │   ├── api/           FastAPI routers
│   │   ├── models/        SQLAlchemy ORM models
│   │   └── db/            session + seeding
│   ├── alembic/           migrations
│   └── tests/             pytest suite (SQLite, low solver time limit)
├── frontend/
│   ├── src/
│   │   ├── lib/           typed API client, types, theme, utils
│   │   ├── pages/         Board, Schedule, Disruptions, Analytics, Entities, Add Data
│   │   └── components/    StatCard, ConflictsWidget, UI primitives
├── scripts/               seed + demo scenarios
├── .github/workflows/     CI
├── start.sh               one-command launcher
└── docker-compose.yml
```

---

## How it works

### Modeling & solving
1. One **optional interval** per interview per allowed day; `AddNoOverlap` per
   student; `AddCumulative` for room×day and panel×company×day; 30-minute slots
   between 09:00 and 17:00.
2. **Weighted objective** (in priority order):
   - `scheduled_interview = 10000` — maximize coverage (dominant)
   - `priority` bonus `{TIER_1: 300, TIER_2: 200, TIER_3: 100}` — favour Tier-1 mass recruiters
   - `earliness_minute = 1` — pack interviews early, reduce waiting
   - `moved_interview = 5000` / `moved_minute = 5` — replan-only churn penalties
3. **Resource coloring** — rooms/panels are assigned by a deterministic greedy
   interval coloring (start-time order, preferring the original resource on
   replans). Keeps the model tiny while guaranteeing no double-booking.
4. **Validation** — every solution is re-validated by a pure validator before
   persistence; the schedule reports `VALID`, or `PARTIAL`/`INFEASIBLE` with
   explicit per-interview reasons.

### Replanning under disruption
Replanning is **validity-based**. If an appointment is still legal in the new
problem it is **frozen** (day + start time) so it never moves; only the affected
region is re-solved. Resources are re-colored freely — time is the scarce
resource (the student), space is fungible (the room).

After solving, the **diff engine** classifies every appointment and emits an
impact summary (students/rooms/panels affected, churn %).

---

## Decision defenses

### What does a "good" schedule mean?
Reported in `GET /api/schedule/metrics` and on the Analytics page:

- **Coverage** — % of shortlists scheduled (dominant; maximised, with reasons for what can't fit).
- **Student clashes** — must be 0 in a VALID schedule.
- **Room / panel utilization** — how saturated the resources are.
- **Average student waiting time** — mean gap between consecutive interviews.
- **Replan churn** — moved bookings ÷ previous scheduled count. A first-class
  cost: a "technically valid" plan that moves 200 appointments to fix a 2-hour
  delay is a disaster.

### Which constraint bends first — and who decides?
- **Who bends:** soft preferences bend first (earliness then scheduling order);
  hard constraints (no overlap, no double-booking) never bend. The final resort
  is coverage — an interview that genuinely can't be placed is left
  `UNSCHEDULED` **with a reason**, never silently dropped.
- **Who decides:** the **coordinator**, via the dashboard. The default policy is
  applied automatically, but the churn penalty and pre/post diff review give the
  coordinator the final call. Transparent, not authoritative.

### How much reshuffling is acceptable?
Churn is minimized and reported. The frozen-region design guarantees unaffected
appointments never move. Observed churn across all four disruption types is
**0%–4.7%** — a 2-hour delay, for instance, moves ~1.4% of bookings.

---

## Measured behaviour (seed 42)

| Disruption | Affected | Moved | Cancelled | Added | Churn |
|---|---|---|---|---|---|
| Company delayed 2h | 33 | 16 | 16 | 1 | 1.43% |
| Panel unavailable | 35 | 12 | 7 | 16 | 1.09% |
| Room unavailable | 61 | 34 | 21 | 6 | 3.06% |
| Student withdrew | 14 | 0 | 13 | 1 | 0.00% |

**Initial solve** (35 companies, 800 students, 20 rooms, 1,123 shortlists):
**1117/1123 scheduled (99.47% coverage), 0 student clashes, 90% room
utilization, `FEASIBLE`/`PARTIAL`** with explicit reasons for the 6 unscheduled.

---

## Getting started

### One command (recommended)

```bash
./start.sh --seed
```

Installs deps if needed, generates the dataset + solves the initial schedule,
then starts the backend (`:8000`) and frontend (`:5173`). Open
**http://localhost:5173**.

> Uses SQLite via `backend/.env` — **no database, Docker, or env vars needed.**

### Manually (two terminals)

```bash
# Terminal 1 — backend
cd backend && python3.11 -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

### Docker Compose

```bash
docker compose up --build   # backend :8000 · frontend :5173 · postgres :5432
```

### Tests

```bash
cd backend && python3.11 -m pytest -q    # 45 tests
```

---

## Adding your own data

From the **Add Data** page (`/add-data`) or the API:

1. **Manual forms** — add a company/student/room/panel/shortlist at a time
   (adding a company auto-provisions its panels).
2. **JSON** — `POST /api/data/import`:
   ```json
   {
     "companies": [{"name":"Acme","priority_tier":"TIER_1","cgpa_cutoff":7.5,"panel_count":2,"available_days":["DAY_1"]}],
     "students": [{"name":"Aman","cgpa":8.1,"branch":"CSE"}],
     "rooms": [{"name":"Room-1","capacity":6}],
     "panels": [{"company_id":"COMP-01","name":"P1"}],
     "shortlists": [{"student_id":"STU-0001","company_id":"COMP-01"}]
   }
   ```
3. **CSV** — `POST /api/data/import/csv` (multipart `entity` + `file`), header
   matching field names, e.g. students: `name,cgpa,branch,year`.

**Reset:** `DELETE /api/data/all`. After adding data, call `POST /api/schedule`
to (re)solve.

> Valid placement days are `DAY_1`–`DAY_4` (fixed dates 2026-08-24 → 08-27).

---

## API reference

| Method | Path | Description |
|---|---|---|
| POST | `/api/generate-data` | Deterministic dataset generator |
| POST | `/api/schedule` | Solve & persist the schedule |
| GET | `/api/schedule` | Active schedule version + interviews |
| GET | `/api/schedule/versions` | List versions |
| GET | `/api/schedule/metrics` | Coverage / clashes / utilization / churn |
| GET | `/api/schedule/conflicts` | Student/room/panel double-bookings |
| GET | `/api/schedule/{version_id}` | A specific version |
| GET | `/api/schedule/{version_id}/changes` | Diff against its parent |
| GET | `/api/companies` · `/students` · `/rooms` · `/panels` | Entities |
| POST | `/api/disruptions` | Record a disruption |
| POST | `/api/replan` | Re-solve around disruptions, return diff |
| POST | `/api/data/{company\|student\|room\|panel\|shortlist}` | Add entity |
| POST | `/api/data/import` · `/api/data/import/csv` | Bulk JSON / CSV |
| DELETE | `/api/data/all` | Wipe all placement data |

Interactive docs: **http://localhost:8000/docs**

---

## Design notes

- **Single-interval-per-day** keeps the model compact and fast (reference solves
  in ~2–10s) at the cost of not allowing a student two rounds with one company
  in the same day.
- **Composite PK** on `interviews` lets replanning append versions without losing
  history, making every change auditable.
- **Configurable weights** (`backend/app/config.py`) expose the whole objective
  so the coverage/priority/churn trade-off can be tuned without touching solver code.

---

## Roadmap / ideas

- Time-window variants (allow two rounds per company per day).
- Multi-week horizons and per-day capacity planning.
- Preferences: student/company priorities beyond tier.
- Export schedule to calendar (ICS) and a printable coordinators' sheet.

---

## License

[MIT](./LICENSE) · © 2026 Amrit Kang
