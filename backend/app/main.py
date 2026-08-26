"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import companies, data, disruptions, panels, rooms, schedule, students
from app.config import settings
from app.db.database import SessionLocal, engine
from app.db.seed import seed_database
from app.models import Company
from app.models.base import Base
from app.services import scheduling_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("placement-scheduler")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenience for local/dev: create tables if they do not exist.
    # Production deployments use Alembic migrations (see README).
    Base.metadata.create_all(bind=engine)

    # First boot on an empty database: seed a deterministic dataset and solve
    # the initial schedule so a fresh deployment is usable out of the box.
    db = SessionLocal()
    try:
        if db.query(Company).count() == 0:
            logger.info("Empty database — generating demo data and initial schedule.")
            seed_database(db, seed=42, force=True)
            scheduling_service.generate_schedule(db, "Initial schedule")
    finally:
        db.close()

    yield


app = FastAPI(title="Placement Week Scheduler", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (companies.router, students.router, rooms.router, panels.router,
               schedule.router, disruptions.router, data.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok", "env": settings.app_env}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "details": {},
            }
        },
    )
