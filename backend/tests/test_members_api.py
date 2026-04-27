from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_list_members_returns_16():
    res = client.get("/members")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 16


def test_member_fields():
    res = client.get("/members")
    member = res.json()[0]
    assert "name" in member
    assert "active" in member
    assert "assignable_day1" in member
    assert "assignable_day2" in member
    assert "assignable_night" in member


def test_ng_entries_empty_initially():
    res = client.get("/ng_entries")
    assert res.status_code == 200
    assert res.json() == []


def test_ng_entry_create_and_list():
    payload = {
        "person_name": "田中",
        "start_date": "2026-05-10",
        "end_date": "2026-05-11",
        "reason": "出張",
    }
    res = client.post("/ng_entries", json=payload)
    assert res.status_code == 201
    assert res.json()["person_name"] == "田中"

    res2 = client.get("/ng_entries")
    names = [e["person_name"] for e in res2.json()]
    assert "田中" in names


def test_history_state_endpoint():
    res = client.get("/history/state")
    assert res.status_code == 200
    data = res.json()
    assert "entries" in data
    assert "people" in data
    assert "total_entries" in data


def test_history_source_endpoint():
    res = client.get("/history/source")
    assert res.status_code == 200
    data = res.json()
    assert data["kind"] in ("default", "upload", "empty")
    assert "label" in data
    assert "row_count" in data
    assert data.get("default_path") == ".docs/previous_data.csv"


def test_export_entries_endpoint():
    payload = [
        {
            "date": "2026-05-02",
            "shift_category": "Day",
            "shift_index": 1,
            "person_name": "田中",
        }
    ]
    res = client.post("/history/export", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert len(res.content) > 0
