"""Disruption and replanning API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Disruption
from app.schemas.disruption import DisruptionCreate, DisruptionOut
from app.schemas.schedule import ReplanRequest, ReplanResponse
from app.services import replanning_service

router = APIRouter(prefix="/api", tags=["disruptions"])


@router.get("/disruptions", response_model=list[DisruptionOut])
def list_disruptions(db: Session = Depends(get_db)):
    return db.query(Disruption).order_by(Disruption.created_at.desc()).all()


@router.post("/disruptions", response_model=DisruptionOut)
def create_disruption(req: DisruptionCreate, db: Session = Depends(get_db)):
    try:
        return replanning_service.apply_disruption(db, req.type, req.entity_id, req.details)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/replan", response_model=ReplanResponse)
def replan(req: ReplanRequest, db: Session = Depends(get_db)):
    try:
        for d in req.disruptions:
            replanning_service.apply_disruption(db, d.type, d.entity_id, d.details)
        result = replanning_service.replan(db, req.reason or "Replan after disruption")
        return ReplanResponse(**result)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except replanning_service.ScheduleValidationError as e:
        raise HTTPException(422, str(e))
