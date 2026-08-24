"""Pydantic schemas for disruptions."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DisruptionCreate(BaseModel):
    type: str  # COMPANY_DELAY | PANEL_UNAVAILABLE | ROOM_UNAVAILABLE | STUDENT_WITHDRAWAL
    entity_id: str
    details: dict = {}


class DisruptionOut(BaseModel):
    id: str
    type: str
    entity_id: str
    effective_from: datetime | None = None
    details: dict
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
