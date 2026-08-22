"""Company ORM model."""
from __future__ import annotations

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    priority_tier: Mapped[str] = mapped_column(String(16), nullable=False)  # TIER_1/2/3
    cgpa_cutoff: Mapped[float] = mapped_column(Float, nullable=False)
    interview_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    panel_count: Mapped[int] = mapped_column(Integer, nullable=False)
    available_days: Mapped[list] = mapped_column(JSON, default=list)  # ["DAY_1", ...]
    # list of {"day": "DAY_1", "start": "09:00", "end": "17:00"}
    availability_windows: Mapped[list] = mapped_column(JSON, default=list)
    delayed_until: Mapped[str | None] = mapped_column(String(8), nullable=True)  # "HH:MM"

    panels: Mapped[list["Panel"]] = relationship(back_populates="company")
