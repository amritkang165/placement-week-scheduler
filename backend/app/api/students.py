"""Student API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Student
from app.schemas.student import StudentOut

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(
    branch: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Student)
    if branch:
        q = q.filter(Student.branch == branch)
    if status:
        q = q.filter(Student.status == status)
    return q.order_by(Student.id).all()
