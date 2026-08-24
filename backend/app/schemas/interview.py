"""Pydantic schemas for interviews."""
from __future__ import annotations

from pydantic import BaseModel


class InterviewOut(BaseModel):
    id: str
    student_id: str
    student_name: str
    company_id: str
    company_name: str
    room_id: str | None = None
    panel_id: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_minutes: int
    status: str
    reason: str | None = None
