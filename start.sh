#!/usr/bin/env bash
# One-command launcher for the Placement Week Scheduler.
# Backend (FastAPI + CP-SAT) on :8000, frontend (Vite) on :5173.
#
# Usage:
#   ./start.sh            # just start
#   ./start.sh --seed     # start, and auto-install deps + generate data + solve
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED=0
for arg in "$@"; do
  case "$arg" in
    --seed) SEED=1 ;;
  esac
done

echo "▸ Checking backend dependencies..."
(cd "$ROOT/backend" && python3.11 -c "import fastapi, sqlalchemy, ortools" 2>/dev/null \
  || python3.11 -m pip install -q -r "$ROOT/backend/requirements.txt")

echo "▸ Checking frontend dependencies..."
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  (cd "$ROOT/frontend" && npm install --silent)
fi

if [ "$SEED" = "1" ]; then
  echo "▸ Generating deterministic dataset + initial schedule..."
  (cd "$ROOT/backend" && python3.11 -c "
from app.db.database import SessionLocal, engine
from app.models.base import Base
from app.db.seed import is_seeded, seed_database
from app.services import scheduling_service
Base.metadata.create_all(bind=engine)
db = SessionLocal()
if not is_seeded(db):
    seed_database(db, seed=42, force=True)
    scheduling_service.generate_schedule(db, 'Initial schedule')
    print('   seeded 42 + solved')
else:
    print('   already seeded')
db.close()
")
fi

echo "▸ Starting backend on http://localhost:8000 ..."
(cd "$ROOT/backend" && python3.11 -m uvicorn app.main:app --port 8000) &
BACK_PID=$!

echo "▸ Starting frontend on http://localhost:5173 ..."
(cd "$ROOT/frontend" && npm run dev) &
FRONT_PID=$!

trap 'echo; echo "Stopping..."; kill $BACK_PID $FRONT_PID 2>/dev/null || true' INT TERM

echo
echo "  ────────────────────────────────────────────────────────────"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000  (docs: /docs)"
echo "   Press Ctrl+C to stop both."
echo "  ────────────────────────────────────────────────────────────"

wait
