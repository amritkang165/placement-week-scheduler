#!/usr/bin/env python3
"""Deterministic seeding script.

Usage:
    python scripts/seed.py                  # seed with default seed = 42
    python scripts/seed.py --seed 7         # seed with a specific value
    python scripts/seed.py --force          # wipe and re-seed
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal, engine  # noqa: E402
from app.db.seed import is_seeded, seed_database  # noqa: E402
from app.models.base import Base  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the placement database.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
    parser.add_argument("--force", action="store_true", help="Wipe existing data first.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if is_seeded(db) and not args.force:
            print("Database already seeded (use --force to reseed).")
            return
        summary = seed_database(db, seed=args.seed, force=args.force)
        print(f"Seeded database with seed={args.seed}:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
