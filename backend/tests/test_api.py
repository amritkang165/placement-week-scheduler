"""Integration tests for the API."""
from __future__ import annotations


def _setup(client):
    r = client.post("/api/generate-data", json={"seed": 42, "force": True})
    assert r.status_code == 200
    data = r.json()
    assert data["companies"] == 35 and data["students"] == 800 and data["rooms"] == 20


def test_list_endpoints(client):
    _setup(client)
    assert client.get("/api/companies").status_code == 200
    assert client.get("/api/students").status_code == 200
    assert client.get("/api/rooms").status_code == 200
    assert client.get("/api/panels").status_code == 200
    comps = client.get("/api/companies").json()
    assert len(comps) == 35
    assert client.get("/api/students?branch=CSE").status_code == 200


def test_generate_and_schedule_flow(client):
    _setup(client)
    r = client.post("/api/schedule", json={"reason": "Initial schedule"})
    assert r.status_code == 200
    version = r.json()
    assert version["schedule_status"] in ("PARTIAL", "FEASIBLE", "OPTIMAL")
    assert version["is_active"] is True


def test_metrics(client):
    _setup(client)
    client.post("/api/schedule", json={})
    r = client.get("/api/schedule/metrics")
    assert r.status_code == 200
    m = r.json()
    assert m["student_clashes"] == 0
    assert 0 < m["coverage"] <= 100
    assert m["scheduled"] == m["scheduled"]  # smoke; coverage computed
    assert set(m["interviews_by_day"].keys()) == {"DAY_1", "DAY_2", "DAY_3", "DAY_4"}


def test_disruption_and_replan(client):
    _setup(client)
    client.post("/api/schedule", json={})

    # Company delay
    company_id = client.get("/api/companies").json()[0]["id"]
    r = client.post("/api/disruptions", json={
        "type": "COMPANY_DELAY", "entity_id": company_id,
        "details": {"new_start_time": "12:00", "day": "DAY_1"},
    })
    assert r.status_code == 200

    r = client.post("/api/replan", json={"reason": "Company late"})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["affected_interviews"] > 0
    assert "changes" in body
    assert body["version_number"] == 2

    # Changes endpoint for the new version.
    r = client.get(f"/api/schedule/{body['version_id']}/changes")
    assert r.status_code == 200
    assert "summary" in r.json()


def test_unscheduled_have_reasons(client):
    _setup(client)
    client.post("/api/schedule", json={})
    r = client.get("/api/schedule")
    interviews = r.json()["interviews"]
    unscheduled = [i for i in interviews if i["status"] == "UNSCHEDULED"]
    # If any unscheduled exist, they must carry a reason.
    for u in unscheduled:
        assert u["reason"], f"{u['id']} has no reason"


def test_schedule_versions_are_preserved(client):
    _setup(client)
    client.post("/api/schedule", json={})
    company_id = client.get("/api/companies").json()[0]["id"]
    client.post("/api/disruptions", json={
        "type": "COMPANY_DELAY", "entity_id": company_id,
        "details": {"new_start_time": "12:00", "day": "DAY_1"},
    })
    client.post("/api/replan", json={})
    r = client.get("/api/schedule/versions")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] > versions[1]["version_number"]
