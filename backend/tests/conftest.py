"""Pytest fixtures.

Sets up a throwaway SQLite database and a low solver time limit so the suite
runs fast, then exposes a DB session and an API TestClient.
"""
from __future__ import annotations

import os
import tempfile

# Must be set before any `app.*` import so the settings/engine pick them up.
_tmp_dir = tempfile.mkdtemp(prefix="placement_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"
os.environ["SOLVER_TIME_LIMIT_SECONDS"] = "3"
os.environ["SOLVER_WORKERS"] = "4"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.db.seed import seed_database  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def seeded_db():
    db_s = SessionLocal()
    seed_database(db_s, seed=42, force=True)
    yield db_s
    db_s.close()


@pytest.fixture
def client(_create_tables):
    with TestClient(app) as c:
        yield c
