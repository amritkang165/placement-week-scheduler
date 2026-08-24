"""Panel API."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Panel
from app.schemas.panel import PanelOut

router = APIRouter(prefix="/api/panels", tags=["panels"])


@router.get("", response_model=list[PanelOut])
def list_panels(db: Session = Depends(get_db)):
    return db.query(Panel).order_by(Panel.id).all()
