"""Pydantic schemas for manual data entry and bulk import."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    id: str | None = None
    name: str
    priority_tier: str = "TIER_3"
    cgpa_cutoff: float = 0.0
    interview_duration_minutes: int = 30
    panel_count: int = 1
    available_days: list[str] = Field(default_factory=lambda: ["DAY_1", "DAY_2", "DAY_3", "DAY_4"])
    availability_windows: list[dict] = Field(default_factory=list)
    delayed_until: str | None = None


class StudentCreate(BaseModel):
    id: str | None = None
    name: str
    cgpa: float
    branch: str = "CSE"
    year: int = 4
    status: str = "ACTIVE"


class RoomCreate(BaseModel):
    id: str | None = None
    name: str
    status: str = "AVAILABLE"
    capacity: int = 6


class PanelCreate(BaseModel):
    id: str | None = None
    company_id: str
    name: str
    status: str = "AVAILABLE"


class ShortlistCreate(BaseModel):
    id: str | None = None
    student_id: str
    company_id: str


class ImportRequest(BaseModel):
    companies: list[CompanyCreate] = Field(default_factory=list)
    students: list[StudentCreate] = Field(default_factory=list)
    rooms: list[RoomCreate] = Field(default_factory=list)
    panels: list[PanelCreate] = Field(default_factory=list)
    shortlists: list[ShortlistCreate] = Field(default_factory=list)


class ImportResult(BaseModel):
    created: dict
    errors: list[str] = Field(default_factory=list)
