<div align="center">

# ⚡ Placement Week Scheduler

*A CP-SAT scheduler & disruption-aware replanner that replaces a coordinated whiteboard with a system that works the day itself.*

[![CI](https://github.com/amritkang165/placement-week-scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/amritkang165/placement-week-scheduler/actions/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-45%20passed-2ea044)](#)
[![Python](https://img.shields.io/badge/python-3.11-4B8BBE)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)](#)
[![React](https://img.shields.io/badge/react-18-61dafb)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

**35 companies · 800 students · 20 rooms · 4 days · 1,123 shortlists**

</div>

---

## Overview

Placement week is where a coordinator's whiteboard collapses daily: hundreds of students shortlisted by overlapping companies, panels merging and dropping, rooms going dark, and students disappearing into other interviews.

This project builds the **decision engine** that replaces it. It produces a feasible, validated schedule in seconds — and when the day goes sideways, it re-plans the **smallest possible slice** of the schedule and reports exactly what changed and who needs to be told.

> **Result on the reference dataset (seed 42):** `1117 / 1123` interviews scheduled (**99.5% coverage**), **0 student clashes**, **90% room utilization**. Replan churn after a 2-hour company delay: **1.4%**.

---

## Table of contents

- [Highlights](#highlights)
- [Tech stack](#tech-stack)
- [Install & run](#install--run)
- [How it works](#how-it-works)
- [Metrics](#metrics)
- [Project structure](#project-structure)
- [API](#api)
- [Tests](#tests)
- [License](#license)

---

## Highlights

| | Feature | What it does |
|---|---|---|
| 🧩 | **Feasibility-first solver** | Never fails silently — unschedulable interviews are reported **with a reason**. |
| 🔄 | **Disruption-aware replanning** | Company delay, panel dropout, room failure, student withdrawal. Minimal upheaval. |
| 🔍 | **Transparent diff** | Classifies every appointment `UNCHANGED / MOVED / ADDED / CANCELLED` and lists who's affected. |
| 🖥️ | **Coordinator dashboard** | Live state, conflict detection, one-click replan + change summary. |
| 📥 | **Bring your own data** | Manual forms, JSON import, or CSV upload for real placement data. |
| 🌗 | **Editorial UI** | Serif headlines, dark mode, a "coordinators' board" aesthetic. |

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

## Install & run

**One command (recommended).** Installs deps, generates the dataset, solves the initial schedule, and starts both servers:

```bash
./start.sh --seed
```

Open **http://localhost:5173** — the board is pre-loaded.

> Uses SQLite via `backend/.env` — **no database, Docker, or environment variables required**.

**Manual — two terminals:**

```bash
# API      → :8000
cd backend && python3.11 -m uvicorn app.main:app --reload --port 8000

# UI       → :5173
cd frontend && npm install && npm run dev
```

**Docker:** `docker compose up --build` · **Docs:** http://localhost:8000/docs

---

## How it works

1. **Model.** One optional interval per interview per allowed day; `AddNoOverlap` per student; `AddCumulative` for room×day and panel×company×day; 30-minute slots from 09:00–17:00.
2. **Objective** (in priority order):
   - `scheduled_interview = 10000` → maximize coverage
   - tier bonus `{TIER_1: 300, TIER_2: 200, TIER_3: 100}` → favour Tier-1 mass recruiters
   - `earliness_minute = 1` → pack interviews early, cut waiting
   - `moved_interview = 5000`, `moved_minute = 5` → replan-only churn penalties
3. **Coloring.** Rooms/panels are assigned by deterministic greedy interval coloring (start-time order, preferring the original resource on replans). The model stays small while guaranteeing no double-booking.
4. **Validate.** Every solution is re-checked by a pure validator before persistence — `VALID`, or `PARTIAL`/`INFEASIBLE` with per-interview reasons.

**Replanning is validity-based.** An appointment still legal in the new problem is **frozen** (day + start time) and never moves; only the affected region is re-solved. Resources are re-colored freely, because time — not the room — is what a student actually depends on.

---

## Metrics

| Metric | Definition |
|---|---|
| Coverage | % of shortlists scheduled. |
| Student clashes | A student double-booked — must be `0` in a VALID schedule. |
| Room / panel utilization | Hours booked ÷ hours available. |
| Avg student wait | Mean gap between consecutive interviews. |
| Replan churn | Moved bookings ÷ previously scheduled. |

Coverage is the dominant goal: an interview that genuinely cannot be placed is left `UNSCHEDULED` **with a reason**, never silently dropped. Soft preferences (earliness, ordering) bend first; hard constraints (no overlap, no double-booking) never do. The coordinator drives the trade-off via the churn penalty and pre/post diff — the system is transparent, not authoritative.

### Measured behaviour (seed 42)

| Disruption | Affected | Moved | Cancelled | Added | Churn |
|---|---|---|---|---|---|
| Company delayed 2h | 33 | 16 | 16 | 1 | 1.43% |
| Panel unavailable | 35 | 12 | 7 | 16 | 1.09% |
| Room unavailable | 61 | 34 | 21 | 6 | 3.06% |
| Student withdrew | 14 | 0 | 13 | 1 | 0.00% |

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

## API

Interactive docs at **`/docs`** on the running API.

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
POST /api/data/{company|student|room|panel|shortlist}   add entity
POST /api/data/import              bulk JSON
POST /api/data/import/csv          bulk CSV
DELETE /api/data/all               reset
```

Add real placement data from the **Add Data** page or via the endpoints above. Valid placement days are `DAY_1`–`DAY_4`, fixed to 2026-08-24 → 08-27.

---

## Tests

```bash
cd backend && python3.11 -m pytest -q     # 45 tests
```

Covers constraints, validator, metrics, the diff engine, the API, and the replanner for all four disruption types (SQLite, low solver time limit).

---

## License

[MIT](./LICENSE) © 2026 Amrit Kang
