from __future__ import annotations


def test_manual_crud_and_solve(client):
    client.delete("/api/data/all")
    r = client.post("/api/data/company", json={
        "name": "Acme", "priority_tier": "TIER_1", "cgpa_cutoff": 7.5,
        "interview_duration_minutes": 30, "panel_count": 1, "available_days": ["DAY_1"],
    })
    assert r.status_code == 200
    company_id = r.json()["id"]

    r = client.post("/api/data/student", json={"name": "Aman", "cgpa": 8.0})
    assert r.status_code == 200
    student_id = r.json()["id"]

    r = client.post("/api/data/room", json={"name": "Room-1"})
    assert r.status_code == 200

    r = client.post("/api/data/shortlist", json={"student_id": student_id, "company_id": company_id})
    assert r.status_code == 200

    r = client.post("/api/schedule", json={})
    assert r.status_code == 200
    assert r.json()["scheduled_count"] == 1


def test_json_import(client):
    client.delete("/api/data/all")
    r = client.post("/api/data/import", json={
        "companies": [{"name": "Beta", "panel_count": 1, "available_days": ["DAY_1"]}],
        "students": [{"name": "Neha", "cgpa": 7.0}],
        "rooms": [{"name": "Room-2"}],
    })
    assert r.status_code == 200
    assert r.json()["errors"] == []
    assert r.json()["created"] == {"companies": 1, "students": 1, "rooms": 1}


def test_csv_import(client):
    client.delete("/api/data/all")
    data = "name,cgpa,branch,year\nRavi,9.1,MECH,4\nSita,7.3,EEE,3"
    r = client.post(
        "/api/data/import/csv",
        data={"entity": "students"},
        files={"file": ("s.csv", data, "text/csv")},
    )
    assert r.status_code == 200
    assert r.json()["created"] == {"students": 2}
    names = {s["name"] for s in client.get("/api/students").json()}
    assert names == {"Ravi", "Sita"}


def test_wipe_all(client):
    client.delete("/api/data/all")
    client.post("/api/data/company", json={"name": "X", "panel_count": 1})
    assert len(client.get("/api/companies").json()) == 1
    r = client.delete("/api/data/all")
    assert r.status_code == 200
    assert len(client.get("/api/companies").json()) == 0


def test_invalid_day_returns_400_not_500(client):
    client.delete("/api/data/all")
    r = client.post("/api/data/company", json={"name": "X", "available_days": ["DAY_9"]})
    assert r.status_code == 400
    assert "DAY_9" in r.json()["detail"]
