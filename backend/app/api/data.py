"""Data ingestion API: manual entity creation and bulk CSV/JSON import."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import (
    AvailabilityWindow,
    Company,
    Interview,
    Panel,
    Room,
    ScheduleVersion,
    Shortlist,
    Student,
)
from app.scheduler.time_utils import DAY_DATES, DAY_KEYS
from app.schemas.company import CompanyOut
from app.schemas.data import (
    CompanyCreate,
    ImportRequest,
    ImportResult,
    PanelCreate,
    RoomCreate,
    ShortlistCreate,
    StudentCreate,
)
from app.schemas.panel import PanelOut
from app.schemas.room import RoomOut
from app.schemas.student import StudentOut

router = APIRouter(prefix="/api/data", tags=["data"])


def _next_id(prefix: str, count: int, pad: int) -> str:
    return f"{prefix}-{count + 1:0{pad}d}"


# --- manual creation -------------------------------------------------------


@router.post("/company", response_model=CompanyOut)
def create_company(req: CompanyCreate, db: Session = Depends(get_db)):
    cid = req.id or _next_id("COMP", db.query(Company).count(), 2)
    if db.get(Company, cid):
        raise HTTPException(409, f"Company {cid} already exists")
    windows = req.availability_windows or [
        {"day": d, "start": "09:00", "end": "17:00"} for d in req.available_days
    ]
    invalid_days = list(
        dict.fromkeys(
            [
                d for d in req.available_days if d not in DAY_DATES
            ] + [w.get("day") for w in windows if w.get("day") not in DAY_DATES]
        )
    )
    if invalid_days:
        raise HTTPException(
            400, f"Unknown placement day(s) {invalid_days}. Valid: {list(DAY_KEYS)}"
        )
    company = Company(
        id=cid,
        name=req.name,
        priority_tier=req.priority_tier,
        cgpa_cutoff=req.cgpa_cutoff,
        interview_duration_minutes=req.interview_duration_minutes,
        panel_count=req.panel_count,
        available_days=req.available_days,
        availability_windows=windows,
        delayed_until=req.delayed_until,
    )
    db.add(company)
    for w in windows:
        day = w["day"]
        db.add(
            AvailabilityWindow(
                resource_type="company",
                resource_id=cid,
                date=datetime.strptime(DAY_DATES[day], "%Y-%m-%d").date(),
                start_time=w["start"],
                end_time=w["end"],
            )
        )
    for p in range(req.panel_count):
        tag = cid.split("-")[-1]
        db.add(
            Panel(
                id=f"PANEL-{tag}-{p + 1:02d}",
                company_id=cid,
                name=f"PANEL-{tag}-{p + 1:02d}",
                status="AVAILABLE",
            )
        )
    db.commit()
    db.refresh(company)
    return company


@router.post("/student", response_model=StudentOut)
def create_student(req: StudentCreate, db: Session = Depends(get_db)):
    sid = req.id or _next_id("STU", db.query(Student).count(), 4)
    if db.get(Student, sid):
        raise HTTPException(409, f"Student {sid} already exists")
    student = Student(
        id=sid, name=req.name, cgpa=req.cgpa, branch=req.branch, year=req.year, status=req.status
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.post("/room", response_model=RoomOut)
def create_room(req: RoomCreate, db: Session = Depends(get_db)):
    rid = req.id or _next_id("ROOM", db.query(Room).count(), 2)
    if db.get(Room, rid):
        raise HTTPException(409, f"Room {rid} already exists")
    room = Room(id=rid, name=req.name, status=req.status, capacity=req.capacity)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.post("/panel", response_model=PanelOut)
def create_panel(req: PanelCreate, db: Session = Depends(get_db)):
    if db.get(Company, req.company_id) is None:
        raise HTTPException(400, f"Company {req.company_id} not found")
    pid = req.id or _next_id("PANEL", db.query(Panel).count(), 2)
    if db.get(Panel, pid):
        raise HTTPException(409, f"Panel {pid} already exists")
    panel = Panel(id=pid, company_id=req.company_id, name=req.name, status=req.status)
    db.add(panel)
    db.commit()
    db.refresh(panel)
    return panel


@router.post("/shortlist", response_model=dict)
def create_shortlist(req: ShortlistCreate, db: Session = Depends(get_db)):
    if db.get(Student, req.student_id) is None:
        raise HTTPException(400, f"Student {req.student_id} not found")
    if db.get(Company, req.company_id) is None:
        raise HTTPException(400, f"Company {req.company_id} not found")
    sid = req.id or _next_id("SL", db.query(Shortlist).count(), 5)
    if db.get(Shortlist, sid):
        raise HTTPException(409, f"Shortlist {sid} already exists")
    db.add(
        Shortlist(
            id=sid,
            student_id=req.student_id,
            company_id=req.company_id,
            shortlisted_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return {"id": sid, "student_id": req.student_id, "company_id": req.company_id}


# --- bulk import -----------------------------------------------------------


def import_row(entity: str, row: dict, db: Session) -> list[str]:
    """Insert one row and return a list of error messages (empty on success)."""
    try:
        if entity == "companies":
            create_company(CompanyCreate(**row), db)
        elif entity == "students":
            create_student(StudentCreate(**row), db)
        elif entity == "rooms":
            create_room(RoomCreate(**row), db)
        elif entity == "panels":
            create_panel(PanelCreate(**row), db)
        elif entity == "shortlists":
            create_shortlist(ShortlistCreate(**row), db)
        else:
            return [f"Unknown entity '{entity}'"]
        return []
    except HTTPException as e:
        return [str(e.detail)]
    except Exception as e:  # noqa: BLE001
        return [f"{type(e).__name__}: {e}"]


@router.post("/import", response_model=ImportResult)
def import_json(req: ImportRequest, db: Session = Depends(get_db)):
    errors: list[str] = []
    created: dict[str, int] = {}
    for entity, rows in [
        ("companies", req.companies),
        ("students", req.students),
        ("rooms", req.rooms),
        ("panels", req.panels),
        ("shortlists", req.shortlists),
    ]:
        ok = 0
        for row in rows:
            errs = import_row(entity, row.model_dump(), db)
            if errs:
                errors.extend(f"{entity}: {e}" for e in errs)
            else:
                ok += 1
        if ok:
            created[entity] = ok
    return ImportResult(created=created, errors=errors)


@router.post("/import/csv", response_model=ImportResult)
async def import_csv(
    entity: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)
):
    text = (await file.read()).decode("utf-8-sig")
    errors: list[str] = []
    ok = 0
    for row in csv.DictReader(io.StringIO(text)):
        row = {k.strip(): v.strip() for k, v in row.items() if k and v is not None}
        errs = import_row(entity, row, db)
        if errs:
            errors.extend(f"CSV row: {e}" for e in errs)
        else:
            ok += 1
    return ImportResult(created={entity: ok}, errors=errors)


@router.delete("/all")
def wipe_data(db: Session = Depends(get_db)):
    for model in (Interview, ScheduleVersion, Shortlist, AvailabilityWindow,
                  Panel, Room, Student, Company):
        db.query(model).delete()
    db.commit()
    return {"status": "cleared"}
