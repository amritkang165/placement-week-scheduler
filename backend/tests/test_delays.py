from app.models import Company, Disruption
from app.scheduler.time_utils import time_str_to_minutes
from app.services.scheduling_service import _active_delays


def test_delay_hours_shifts_all_windows(seeded_db):
    company = seeded_db.query(Company).filter(Company.delayed_until.is_(None)).first()

    seeded_db.add(
        Disruption(
            id="DIS-TEST",
            type="COMPANY_DELAY",
            entity_id=company.id,
            details={"delay_hours": 2},
            status="ACTIVE",
        )
    )
    seeded_db.commit()

    delay = _active_delays(seeded_db)
    assert company.id in delay
    # Every availability day is shifted later.
    for w in company.availability_windows or []:
        assert w["day"] in delay[company.id]
        assert delay[company.id][w["day"]] > time_str_to_minutes(w["start"])
