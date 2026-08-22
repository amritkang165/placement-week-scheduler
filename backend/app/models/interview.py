"""Interview ORM model.

An interview row is created for every shortlist edge (student x company).
Scheduled interviews carry date/time/room/panel; unscheduled ones carry a
`reason` explaining why they could not be placed.
"""
from __future__ import annotations

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    schedule_version_id: Mapped[str] = mapped_column(
        ForeignKey("schedule_versions.id"), primary_key=True, index=True
    )
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    room_id: Mapped[str | None] = mapped_column(ForeignKey("rooms.id"), nullable=True)
    panel_id: Mapped[str | None] = mapped_column(ForeignKey("panels.id"), nullable=True)
    date: Mapped[str | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="UNSCHEDULED")
    reason: Mapped[str | None] = mapped_column(String(64), nullable=True)

    schedule_version: Mapped["ScheduleVersion"] = relationship(back_populates="interviews")
