"""Pydantic schemas for companies."""
from __future__ import annotations

from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: str
    name: str
    priority_tier: str
    cgpa_cutoff: float
    interview_duration_minutes: int
    panel_count: int
    available_days: list[str]
    availability_windows: list[dict]
    delayed_until: str | None = None

    model_config = {"from_attributes": True}
