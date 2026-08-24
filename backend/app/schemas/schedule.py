"""Pydantic schemas for schedule, metrics, and replan responses."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.disruption import DisruptionCreate
from app.schemas.interview import InterviewOut


class ScheduleVersionOut(BaseModel):
    id: str
    version_number: int
    reason: str
    previous_version_id: str | None = None
    solver_status: str
    schedule_status: str
    is_active: bool
    created_at: datetime | None = None
    scheduled_count: int = 0
    unscheduled_count: int = 0
    cancelled_count: int = 0


class ScheduleResponse(BaseModel):
    version: ScheduleVersionOut
    interviews: list[InterviewOut]


class MetricsOut(BaseModel):
    total: int
    scheduled: int
    unscheduled: int
    coverage: float
    student_clashes: int
    room_utilization: float
    panel_utilization: float
    avg_wait_minutes: float
    replan_churn: float
    solver_status: str
    schedule_status: str
    interviews_by_day: dict
    interviews_by_tier: dict
    companies: int = 0
    students: int = 0
    rooms: int = 0
    panels: int = 0


class SlotOut(BaseModel):
    date: str | None = None
    start: str | None = None
    end: str | None = None
    room_id: str | None = None
    panel_id: str | None = None


class ChangeItem(BaseModel):
    interview_id: str
    student_id: str
    student_name: str
    company_id: str
    company_name: str
    change_type: str
    before: SlotOut | None = None
    after: SlotOut | None = None
    reason: str | None = None


class ConflictOut(BaseModel):
    conflict_id: str
    type: str  # STUDENT_CLASH | ROOM_CLASH | PANEL_CLASH
    entity_id: str
    message: str
    interview_ids: list[str]
    involved: list[dict]


class ReplanRequest(BaseModel):
    disruptions: list[DisruptionCreate] = []
    reason: str | None = None


class ReplanResponse(BaseModel):
    version_id: str
    version_number: int
    solver_status: str
    schedule_status: str
    reason: str
    summary: dict
    changes: list[ChangeItem]


class GenerateDataRequest(BaseModel):
    seed: int = 42
    force: bool = False


class ScheduleRequest(BaseModel):
    reason: str = "Initial schedule"
