"""Availability window ORM model.

A generic model that can represent availability for companies, panels, rooms,
and (potentially) students. `resource_type` is one of COMPANY/PANEL/ROOM/STUDENT.
"""
from __future__ import annotations

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AvailabilityWindow(Base, TimestampMixin):
    __tablename__ = "availability_windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_type: Mapped[str] = mapped_column(String(16), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(8), nullable=False)  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(8), nullable=False)    # "HH:MM"
