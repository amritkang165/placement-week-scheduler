"""Pydantic schemas for panels."""
from __future__ import annotations

from pydantic import BaseModel


class PanelOut(BaseModel):
    id: str
    company_id: str
    name: str
    status: str

    model_config = {"from_attributes": True}
