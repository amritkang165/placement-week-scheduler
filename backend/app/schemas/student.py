"""Pydantic schemas for students."""
from __future__ import annotations

from pydantic import BaseModel


class StudentOut(BaseModel):
    id: str
    name: str
    cgpa: float
    branch: str
    year: int
    status: str

    model_config = {"from_attributes": True}
