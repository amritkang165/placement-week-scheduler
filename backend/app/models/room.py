"""Room ORM model."""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="AVAILABLE")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
