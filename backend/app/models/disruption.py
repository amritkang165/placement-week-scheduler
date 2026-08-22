"""Disruption ORM model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Disruption(Base, TimestampMixin):
    __tablename__ = "disruptions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # COMPANY_DELAY, ...
    entity_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    schedule_version_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
