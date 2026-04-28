import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import manual_staff as manual_staff_mod

client = TestClient(app)


@pytest.fixture()
def manual_staff_path(tmp_path, monkeypatch):
    p = tmp_path / "manual_staff.json"
    monkeypatch.setattr(manual_staff_mod, "_manual_staff_file", lambda: p)
    return p


def test_manual_staff_empty(manual_staff_path):
    assert client.get("/manual_staff").json() == []
    assert client.get("/api/manual_staff").json() == []


def test_manual_staff_put_roundtrip(manual_staff_path):
    payload = [{"name": "山田"}, {"name": "佐藤"}]
    put = client.put("/manual_staff", json=payload)
    assert put.status_code == 200
    assert put.json() == payload
    assert manual_staff_path.exists()
    get = client.get("/manual_staff")
    assert get.json() == payload
