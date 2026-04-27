import pytest
import shutil
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import _SETTINGS_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_settings():
    backup = _SETTINGS_PATH.with_suffix(".yaml.bak")
    shutil.copy2(_SETTINGS_PATH, backup)
    yield
    shutil.copy2(backup, _SETTINGS_PATH)
    backup.unlink()


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


def test_create_member():
    payload = {
        "name": "テスト太郎",
        "assignable_day1": True,
        "assignable_day2": False,
        "assignable_night": True,
    }
    res = client.post("/members", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "テスト太郎"
    assert data["active"] is True
    assert data["assignable_day1"] is True
    assert data["assignable_day2"] is False
    assert data["assignable_night"] is True

    res2 = client.get("/members")
    names = [m["name"] for m in res2.json()]
    assert "テスト太郎" in names


def test_create_member_duplicate():
    payload = {"name": "丸岡"}
    res = client.post("/members", json=payload)
    assert res.status_code == 409


def test_create_and_delete_member():
    payload = {"name": "削除用テスト"}
    create_res = client.post("/members", json=payload)
    assert create_res.status_code == 201

    del_res = client.delete("/members/削除用テスト")
    assert del_res.status_code == 204

    list_res = client.get("/members")
    names = [m["name"] for m in list_res.json()]
    assert "削除用テスト" not in names


def test_delete_member_not_found():
    res = client.delete("/members/存在しない名前")
    assert res.status_code == 404


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
