import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestNGBulkAPI:
    def test_bulk_parse_day(self):
        text = "幅下孝一\n5/10、5/17、6/21\n新井洋介\n5/3,6/6"
        res = client.post("/ng_entries/bulk_parse", json={
            "text": text,
            "default_year": 2025,
            "shift_type": "day"
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["person_name"] == "幅下孝一"
        assert len(data["items"][0]["dates"]) == 3

    def test_bulk_parse_night(self):
        text = "髙田明良\n5/10,17,23,24,31, 6/7,14"
        res = client.post("/ng_entries/bulk_parse", json={
            "text": text,
            "default_year": 2025,
            "shift_type": "night"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["items"][0]["person_name"] == "髙田明良"
        assert len(data["items"][0]["dates"]) == 7

    def test_bulk_register_and_list(self):
        # 事前にリストをクリアする手段がないため、インメモリストア上で追記される
        items = [
            {"person_name": "テスト太郎", "dates": ["2025-05-10", "2025-05-17"]},
        ]
        res = client.post("/ng_entries/bulk", json={
            "items": items,
            "shift_type": "day"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["registered"] == 2

        # リスト確認
        list_res = client.get("/ng_entries")
        assert list_res.status_code == 200
        entries = list_res.json()
        assert any(e["person_name"] == "テスト太郎" and e["reason"] == "日勤NG" for e in entries)
