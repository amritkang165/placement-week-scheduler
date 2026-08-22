"""Deterministic, seedable placement-data generator.

Produces realistic placement-season data: 35 companies across three priority
tiers, 800 students with a non-uniform CGPA distribution, 20 rooms, panels per
company, and shortlists that naturally create scheduling pressure (top
students shortlisted by many companies, mass recruiters shortlisting hundreds).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.scheduler.time_utils import (
    BRANCHES,
    DAY_DATES,
    DAY_KEYS,
    OPERATING_END_MIN,
    OPERATING_START_MIN,
    TIERS,
    minutes_to_time_str,
)

# ---------------------------------------------------------------------------
# Pure dataclasses describing generated data (mapped to ORM by the seeder).
# ---------------------------------------------------------------------------


@dataclass
class CompanySpec:
    id: str
    name: str
    priority_tier: str
    cgpa_cutoff: float
    interview_duration_minutes: int
    panel_count: int
    available_days: list[str]
    availability_windows: list[dict]
    shortlist_target: int = 0
    delayed_until: str | None = None


@dataclass
class StudentSpec:
    id: str
    name: str
    cgpa: float
    branch: str
    year: int
    status: str = "ACTIVE"


@dataclass
class RoomSpec:
    id: str
    name: str
    status: str
    capacity: int


@dataclass
class PanelSpec:
    id: str
    company_id: str
    name: str
    status: str = "AVAILABLE"


@dataclass
class ShortlistSpec:
    id: str
    student_id: str
    company_id: str


@dataclass
class AvailabilityWindowSpec:
    resource_type: str
    resource_id: str
    date: str
    start_time: str
    end_time: str


@dataclass
class GeneratedData:
    companies: list[CompanySpec] = field(default_factory=list)
    students: list[StudentSpec] = field(default_factory=list)
    rooms: list[RoomSpec] = field(default_factory=list)
    panels: list[PanelSpec] = field(default_factory=list)
    shortlists: list[ShortlistSpec] = field(default_factory=list)
    availability_windows: list[AvailabilityWindowSpec] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Company / student name pools.
# ---------------------------------------------------------------------------

_TIER1_NAMES = [
    "Titan Infosystems", "Vertex Technologies", "NovaServe Solutions",
    "GlobalSoft Corp", "Apex Digital", "Skyward Analytics",
    "BlueOrbit Tech", "Meridian Consulting", "Stratagem IT", "Horizon Systems",
]
_TIER2_NAMES = [
    "Crestline Software", "Nimbus Works", "Orion Embedded", "PulseData Labs",
    "Greenfield Energy", "Summit Cloud", "Ridgeway Semiconductors",
    "Vantage Networks", "Coral Robotics", "Falcon Analytics", "Lumina Design",
    "Terraform Engineering",
]
_TIER3_NAMES = [
    "Quanticore AI", "Helios Research", "Aurora Fintech", "Zephyr Aerospace",
    "Obsidian Security", "Nebula Ventures", "Paragon Labs", "Cinder Biotech",
    "Eclipse Motors", "Radiant Semis", "Vortex Systems", "Zenith Capital",
    "Halo Defense",
]

_FIRST_NAMES = [
    "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Sneha", "Arjun", "Divya",
    "Karan", "Ishita", "Aditya", "Meera", "Rahul", "Pooja", "Siddharth",
    "Neha", "Kunal", "Shreya", "Nikhil", "Anjali", "Varun", "Tanvi",
    "Harsh", "Ritika", "Aman", "Kavya", "Dev", "Sakshi", "Ishaan", "Nandini",
    "Manish", "Pallavi", "Gaurav", "Lakshmi", "Suraj", "Deepika", "Alok",
    "Mansi", "Pranav", "Ankita",
]
_LAST_NAMES = [
    "Sharma", "Patel", "Reddy", "Kumar", "Iyer", "Nair", "Gupta", "Verma",
    "Singh", "Mehta", "Joshi", "Rao", "Das", "Chopra", "Bose", "Kulkarni",
    "Menon", "Pillai", "Saxena", "Malhotra", "Desai", "Bhat", "Hegde",
    "Choudhary", "Tiwari", "Mishra", "Kapoor", "Agarwal", "Srivastava",
    "Nayak", "Khan", "Rathore", "Sethi", "Kohli", "Pandey", "Acharya",
    "Banerjee", "Dutta", "Ghosh", "Bajaj",
]


def _weighted_sample_no_replace(rng: random.Random, items: list, weights: list[float], k: int) -> list:
    """Deterministic weighted sampling without replacement (exponential race)."""
    if k <= 0:
        return []
    if k >= len(items):
        return list(items)
    keys = [rng.random() ** (1.0 / max(w, 1e-9)) for w in weights]
    order = sorted(range(len(items)), key=lambda i: keys[i], reverse=True)
    return [items[i] for i in order[:k]]


def generate_data(seed: int = 42) -> GeneratedData:
    rng = random.Random(seed)
    data = GeneratedData()

    # ------------------------------------------------------------------ rooms
    for i in range(1, 21):
        data.rooms.append(
            RoomSpec(
                id=f"ROOM-{i:02d}",
                name=f"ROOM-{i:02d}",
                status="AVAILABLE",
                capacity=rng.choice([4, 5, 6, 8, 10]),
            )
        )

    # -------------------------------------------------------------- companies
    companies: list[CompanySpec] = []
    # (tier, names, duration choices, panel range, cutoff range, days range, shortlist range)
    tier_specs = {
        "TIER_1": (_TIER1_NAMES, [20, 30], (3, 6), (6.0, 7.0), (2, 4), (35, 50)),
        "TIER_2": (_TIER2_NAMES, [30, 45], (2, 4), (6.5, 7.5), (2, 4), (20, 30)),
        "TIER_3": (_TIER3_NAMES, [45, 60], (1, 2), (7.5, 9.0), (1, 3), (8, 14)),
    }
    for tier in TIERS:
        names, durations, p_range, c_range, d_range, s_range = tier_specs[tier]
        for idx, name in enumerate(names, start=1):
            comp_num = len(companies) + 1
            panel_count = rng.randint(*p_range)
            duration = rng.choice(durations)
            cgpa_cutoff = round(rng.uniform(*c_range), 2)
            n_days = rng.randint(*d_range)
            available_days = rng.sample(list(DAY_KEYS), n_days)
            available_days = sorted(available_days, key=lambda d: DAY_KEYS.index(d))
            # First few tier-1 companies are "mass recruiters" with very large
            # shortlists; the rest use the normal range.
            if tier == "TIER_1" and idx <= 4:
                shortlist_target = rng.randint(90, 120)
            else:
                shortlist_target = rng.randint(*s_range)

            windows = []
            for day in available_days:
                start = OPERATING_START_MIN
                end = OPERATING_END_MIN
                # slight realistic variation in some company windows
                if rng.random() < 0.25:
                    start += rng.choice([0, 15, 30])
                if rng.random() < 0.25:
                    end -= rng.choice([0, 15, 30])
                windows.append(
                    {
                        "day": day,
                        "start": minutes_to_time_str(start),
                        "end": minutes_to_time_str(end),
                    }
                )

            company = CompanySpec(
                id=f"COMP-{comp_num:02d}",
                name=name,
                priority_tier=tier,
                cgpa_cutoff=cgpa_cutoff,
                interview_duration_minutes=duration,
                panel_count=panel_count,
                available_days=available_days,
                availability_windows=windows,
                shortlist_target=shortlist_target,
            )
            companies.append(company)
    data.companies = companies

    # ---------------------------------------------------------------- panels
    for company in companies:
        comp_num = int(company.id.split("-")[1])
        for p in range(1, company.panel_count + 1):
            data.panels.append(
                PanelSpec(
                    id=f"PANEL-{comp_num:02d}-{p:02d}",
                    company_id=company.id,
                    name=f"{company.name} — Panel {p}",
                )
            )

    # -------------------------------------------------------------- students
    students: list[StudentSpec] = []
    branch_weights = [0.30, 0.20, 0.20, 0.10, 0.10, 0.10]
    for i in range(1, 801):
        # Non-uniform CGPA: bell curve around 7.8 clamped to [6.0, 10.0].
        cgpa = round(min(10.0, max(6.0, rng.gauss(7.8, 1.15))), 2)
        branch = rng.choices(BRANCHES, weights=branch_weights, k=1)[0]
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        students.append(
            StudentSpec(
                id=f"STU-{i:04d}",
                name=f"{first} {last}",
                cgpa=cgpa,
                branch=branch,
                year=4,
            )
        )
    data.students = students

    # ------------------------------------------------------------ shortlists
    shortlists: list[ShortlistSpec] = []
    sl_seq = 0
    for company in companies:
        eligible = [s for s in students if s.cgpa >= company.cgpa_cutoff]
        weights = [(s.cgpa - company.cgpa_cutoff) ** 2 + 0.25 for s in eligible]
        target = company.shortlist_target
        picked = _weighted_sample_no_replace(rng, eligible, weights, target)
        for student in picked:
            sl_seq += 1
            shortlists.append(
                ShortlistSpec(
                    id=f"SL-{sl_seq:05d}",
                    student_id=student.id,
                    company_id=company.id,
                )
            )
    data.shortlists = shortlists

    # ---------------------------------------------------- availability windows
    windows: list[AvailabilityWindowSpec] = []
    # Company + panel windows follow the company availability windows.
    for company in companies:
        for w in company.availability_windows:
            date = DAY_DATES[w["day"]]
            windows.append(
                AvailabilityWindowSpec("COMPANY", company.id, date, w["start"], w["end"])
            )
            for panel in [p for p in data.panels if p.company_id == company.id]:
                windows.append(
                    AvailabilityWindowSpec("PANEL", panel.id, date, w["start"], w["end"])
                )
    # Rooms are available for the full operating window on every day.
    for room in data.rooms:
        for day in DAY_KEYS:
            windows.append(
                AvailabilityWindowSpec(
                    "ROOM",
                    room.id,
                    DAY_DATES[day],
                    minutes_to_time_str(OPERATING_START_MIN),
                    minutes_to_time_str(OPERATING_END_MIN),
                )
            )

    data.availability_windows = windows
    return data
