# Placement Week Scheduler

A production-grade scheduler + disruption-aware replanner for placement week,
built as the Mirai Labs (Assignment A) technical assessment. It turns a
whiteboard that "collapses daily" into a CP-SAT-powered daily-driver for a
stressed placement coordinator.

## Tech stack

- **Solver:** Google OR-Tools CP-SAT (`ortools`)
- **Backend:** FastAPI + SQLAlchemy + Pydantic + Alembic
- **Frontend:** React + Vite + TypeScript + Tailwind + Recharts
- **Storage:** PostgreSQL (SQLite for local dev / tests)

## High-level architecture

```
backend/
  app/
    generator/     deterministic realistic dataset generator
    scheduler/     problem model, constraints, objective, CP-SAT solver, validator
    services/      scheduling, replanning, metrics, diff engine (pure functions)
    schemas/       Pydantic API contract
    api/           FastAPI routers
  alembic/         migrations
  tests/           pytest suite (SQLite, low solver time limit)
frontend/
  src/
    lib/           typed API client, types, utils
    pages/         Dashboard, Schedule, Disruptions(Replan), Analytics, Entities
    components/    StatCard, ConflictsWidget, UI primitives
```

## Data model

- **Company** – priority tier, CGPA cutoff, per-interview duration, panel count,
  available days + per-day availability windows.
- **Student** – CGPA, branch, year, status.
- **Shortlist** – an edge `(student, company)` that must be scheduled.
- **Interview** – the scheduled result of a shortlist; primary key is the
  composite `(shortlist_id, schedule_version_id)` so each shortlist can carry
  one row per version (SCHEDULED / UNSCHEDULED / CANCELLED).
- **ScheduleVersion** – a snapshot; replanning appends a new version and links
  `previous_version_id` (so the diff is always available).
- **Disruption** – an injected event (`COMPANY_DELAY`, `PANEL_UNAVAILABLE`,
  `ROOM_UNAVAILABLE`, `STUDENT_WITHDRAWAL`).

## How scheduling works

1. **Model** – one optional interval per interview per allowed day, `AddNoOverlap`
   per student, `AddCumulative` for room×day and panel×company×day, plus a
   fixed-slots domain (30-minute slots between 09:00 and 17:00).
2. **Objective (weighted, in priority order):**
   - `scheduled_interview = 10000` – maximize coverage (dominant term);
   - `priority` bonus `{TIER_1: 300, TIER_2: 200, TIER_3: 100}` – favour Tier-1 mass recruiters;
   - `earliness_minute = 1` – pack interviews early to reduce student waiting;
   - `moved_interview = 5000` / `moved_minute = 5` – replan-only penalties so
     the solver minimises reshuffling.
3. **Coloring** – rooms/panels are assigned by a deterministic greedy interval
   coloring (start-time order, preferring the original resource on replans),
   which keeps the CP-SAT model small while guaranteeing no double-booking.
4. **Validation** – every solution is re-validated by a pure `validator` before
   persistence; the schedule reports `VALID`, or `PARTIAL`/`INFEASIBLE` with
   explicit per-interview reasons.

## Replanning under disruption

Replanning is **validity-based**. `_valid_in_problem(interview, problem)` decides
whether an existing appointment is still legal in the new problem; if it is, it is
**frozen** so it never moves. Only the affected region is re-solved.

- **TIME is frozen** (day + start time) whenever an appointment stays valid.
- **Resources are re-colored freely** – this avoids the list-colouring infeasibility
  that would otherwise occur (e.g. a room failure that blocks every legal room for
  a frozen time would force an unacceptable move). Time is the precious resource
  (the student), space is fungible (the room).

After solving, the **diff engine** classifies every appointment as
`UNCHANGED / MOVED / ADDED / CANCELLED / UNSCHEDULED` and produces an impact
summary (students/rooms/panels affected, churn %).

## Decision defenses (the "must defend" questions)

### What does a 'good' schedule mean?
Reported metrics (see `GET /api/schedule/metrics` and the Analytics page):

- **Coverage** – % of shortlists scheduled (the dominant goal; a perfect schedule
  is usually impossible, so we maximise it and say why the rest are unscheduled).
- **Student clashes** – a student double-booked; must be 0 in a VALID schedule.
- **Room / panel utilization** – how saturated the resources are.
- **Average student waiting time** – mean gap between consecutive interviews.
- **Replan churn** – moved bookings / previous scheduled count. Churn is a first-class
  cost, not a side effect: a "technically valid" plan that moves 200 appointments
  to fix a 2-hour delay is a disaster.

### Which constraint bends first — and who decides?
- **Who bends:** the least-important *soft* preferences bend first (earliness then
  scheduling order), while the *hard* constraints (no student overlap, no room/panel
  double-booking) never bend. The absolute final resort is coverage: an interview
  that genuinely cannot be placed is left `UNSCHEDULED` **with a reason**, never
  silently dropped.
- **Who decides:** the **coordinator**, via the dashboard. The default policy
  (coverage > Tier priority > earliness) is applied automatically, but the churn
  penalty and the ability to review the diff before/after a replan give the
  coordinator the final call. The system is transparent rather than authoritative.

### How much reshuffling is acceptable during a replan?
Churn is explicitly minimized and reported. The frozen-region design guarantees
that unaffected appointments never move. On the reference dataset the observed
churn across all four disruption types is **0%–4.7%** (see "Measured behaviour"
below) — a 2-hour company delay, for instance, moves ~1.4% of bookings. This is
the difference between "technically valid" and "practically usable".

## Measured behaviour (seed 42)

| Disruption | Affected | Moved | Cancelled | Added | Churn |
|---|---|---|---|---|---|
| Company delayed 2h | 33 | 16 | 16 | 1 | 1.43% |
| Panel unavailable | 35 | 12 | 7 | 16 | 1.09% |
| Room unavailable | 61 | 34 | 21 | 6 | 3.06% |
| Student withdrew | 14 | 0 | 13 | 1 | 0.00% |

Initial solve (35 companies, 800 students, 20 rooms, 1123 shortlists):
**1117/1123 scheduled (99.47% coverage), 0 student clashes, 90% room utilization,
`FEASIBLE`/`PARTIAL`** with explicit reasons for the 6 unscheduled shortlists.

## Running locally

### Quickest — one command

From the project root:

```bash
./start.sh --seed
```

This installs dependencies (if needed), generates the dataset + solves the
initial schedule, then starts the backend (`:8000`) and frontend (`:5173`)
together. Open **http://localhost:5173**.

> It uses SQLite by default via `backend/.env`, so **no database, no Docker,
> and no environment variables are needed**.

### Manually — two terminals

Backend (`:8000`):

```bash
cd backend
python3.11 -m uvicorn app.main:app --reload --port 8000
```

Frontend (`:5173`):

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to :8000)
```

API docs: http://localhost:8000/docs

### Tests

```bash
cd backend && python3.11 -m pytest -q     # 45 tests
```

### Docker Compose

```bash
docker compose up --build
# backend :8000 · frontend :5173 · postgres :5432
```

### Adding your own data

The generator is only one source. You can load real placement data three ways
from the **Add Data** page (`/add-data`), or via the API directly:

1. **Manual forms** – add one company, student, room, panel, or shortlist at a
   time (adding a company auto-provisions its panels).
2. **JSON bulk import** – `POST /api/data/import` with:
   ```json
   {
     "companies": [{"name":"Acme","priority_tier":"TIER_1","cgpa_cutoff":7.5,"panel_count":2,"available_days":["DAY_1"]}],
     "students": [{"name":"Aman","cgpa":8.1,"branch":"CSE"}],
     "rooms": [{"name":"Room-1","capacity":6}],
     "panels": [{"company_id":"COMP-01","name":"P1"}],
     "shortlists": [{"student_id":"STU-0001","company_id":"COMP-01"}]
   }
   ```
3. **CSV bulk import** – `POST /api/data/import/csv` (multipart form: `entity` +
   `file`), with a CSV header matching the field names, e.g. students:
   `name,cgpa,branch,year`.

**Reset:** `DELETE /api/data/all` wipes all placement data. After adding data,
call `POST /api/schedule` to (re)solve.

### 3. Tests

```bash
cd backend && python3.11 -m pytest -q     # 44 tests
```

### 4. Docker Compose

```bash
docker compose up --build
# backend :8000 · frontend :5173 · postgres :5432
```

## API surface (summary)

| Method | Path | Description |
|---|---|---|
| POST | `/api/generate-data` | Deterministic dataset generator (seed, force) |
| POST | `/api/schedule` | Solve & persist the initial schedule |
| GET | `/api/schedule` | The active schedule version + interviews |
| GET | `/api/schedule/versions` | List versions |
| GET | `/api/schedule/metrics` | Coverage / clashes / utilization / churn |
| GET | `/api/schedule/conflicts` | Detect student/room/panel double-bookings |
| GET | `/api/schedule/{version_id}` | A specific version |
| GET | `/api/schedule/{version_id}/changes` | Diff against its parent |
| GET | `/api/companies`, `/api/students`, `/api/rooms`, `/api/panels` | Entities |
| POST | `/api/disruptions` | Record a disruption |
| POST | `/api/replan` | Re-solve around disruptions, return the diff |
| POST | `/api/data/company`, `/student`, `/room`, `/panel`, `/shortlist` | Add entity manually |
| POST | `/api/data/import` | Bulk JSON import |
| POST | `/api/data/import/csv` | Bulk CSV import (multipart) |
| DELETE | `/api/data/all` | Wipe all placement data |

## Design notes / trade-offs

- **Single-interval-per-day** keeps the model compact and fast (references solve in
  ~2–10s) at the cost of not allowing a student two rounds with the same company in
  one day.
- **Composite PK** on `interviews` lets replanning append versions without losing
  history, making every change auditable.
- **Configurable weights** (`app/config.py`) expose the entire objective so the
  coverage/priority/churn trade-off can be tuned without touching solver code.
