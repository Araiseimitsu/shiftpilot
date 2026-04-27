from datetime import date
from pathlib import Path

import pytest

from backend.app.core.csv_io import dump_csv, load_csv
from backend.app.schemas.shift import ShiftCategory, ShiftEntry

_DOCS_CSV = Path(__file__).parents[2] / ".docs" / "previous_data.csv"


def test_load_previous_csv():
    pytest.importorskip("csv")
    if not _DOCS_CSV.exists():
        pytest.skip("previous_data.csv が見つかりません")
    entries = load_csv(_DOCS_CSV)
    assert len(entries) > 0
    for e in entries:
        assert e.person_name
        assert e.shift_category in (ShiftCategory.DAY, ShiftCategory.NIGHT)


def test_dump_and_reload_roundtrip(tmp_path: Path):
    entries = [
        ShiftEntry(date=date(2026, 5, 2), shift_category=ShiftCategory.DAY, shift_index=1, person_name="田中"),
        ShiftEntry(date=date(2026, 5, 2), shift_category=ShiftCategory.DAY, shift_index=2, person_name="木村"),
        ShiftEntry(date=date(2026, 5, 4), shift_category=ShiftCategory.NIGHT, shift_index=1, person_name="斉藤"),
    ]
    csv_bytes = dump_csv(entries)
    out = tmp_path / "test.csv"
    out.write_bytes(csv_bytes)
    reloaded = load_csv(out)
    assert len(reloaded) == 3
    names = {e.person_name for e in reloaded}
    assert names == {"田中", "木村", "斉藤"}


def test_night_shift_index_is_always_1():
    if not _DOCS_CSV.exists():
        pytest.skip("previous_data.csv が見つかりません")
    entries = load_csv(_DOCS_CSV)
    night = [e for e in entries if e.shift_category == ShiftCategory.NIGHT]
    for e in night:
        assert e.shift_index == 1
