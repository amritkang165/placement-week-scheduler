"""Pydantic schemas for rooms."""
from __future__ import annotations

from pydantic import BaseModel


class RoomOut(BaseModel):
    id: str
    name: str
    status: str
    capacity: int

    model_config = {"from_attributes": True}
