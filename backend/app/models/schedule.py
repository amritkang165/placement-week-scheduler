"""Schedule version ORM model (immutable schedule snapshots)."""
from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ScheduleVersion(Base, TimestampMixin):
    __tablename__ = "schedule_versions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(256), nullable=False, default="Initial schedule")
    previous_version_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    solver_status: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    schedule_status: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    interviews: Mapped[list["Interview"]] = relationship(back_populates="schedule_version")
