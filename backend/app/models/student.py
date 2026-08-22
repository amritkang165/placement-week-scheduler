"""Student ORM model."""
from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False)
    branch: Mapped[str] = mapped_column(String(16), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")

    shortlists: Mapped[list["Shortlist"]] = relationship(back_populates="student")
