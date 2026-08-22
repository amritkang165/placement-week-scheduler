"""Import all ORM models so Alembic and metadata discovery see them."""
from app.models.base import Base
from app.models.availability_window import AvailabilityWindow
from app.models.company import Company
from app.models.disruption import Disruption
from app.models.interview import Interview
from app.models.panel import Panel
from app.models.room import Room
from app.models.schedule import ScheduleVersion
from app.models.shortlist import Shortlist
from app.models.student import Student

__all__ = [
    "Base",
    "AvailabilityWindow",
    "Company",
    "Disruption",
    "Interview",
    "Panel",
    "Room",
    "ScheduleVersion",
    "Shortlist",
    "Student",
]
