from datetime import date

from backend.app.core.history_state import (
    build_history_state,
    next_assignment_period_end,
    normalize_entries,
)
from backend.app.schemas.shift import ShiftCategory, ShiftEntry


def test_next_assignment_period_end_june_to_august():
    assert next_assignment_period_end(date(2026, 6, 21)) == date(2026, 8, 20)


def test_next_assignment_period_end_december_rolls_year():
    assert next_assignment_period_end(date(2026, 12, 21)) == date(2027, 2, 20)


def test_normalize_entries_keeps_last_assignment_for_same_slot():
    entries = [
        ShiftEntry(date=date(2026, 5, 2), shift_category=ShiftCategory.DAY, shift_index=1, person_name="田中"),
        ShiftEntry(date=date(2026, 5, 2), shift_category=ShiftCategory.DAY, shift_index=1, person_name="木村"),
    ]

    normalized = normalize_entries(entries)

    assert len(normalized) == 1
    assert normalized[0].person_name == "木村"


def test_build_history_state_counts_by_person_and_category():
    entries = [
        ShiftEntry(date=date(2026, 5, 2), shift_category=ShiftCategory.DAY, shift_index=1, person_name="田中"),
        ShiftEntry(date=date(2026, 5, 3), shift_category=ShiftCategory.DAY, shift_index=2, person_name="田中"),
        ShiftEntry(date=date(2026, 5, 4), shift_category=ShiftCategory.NIGHT, shift_index=1, person_name="木村"),
    ]

    state = build_history_state(entries)
    people = {person.person_name: person for person in state.people}

    assert state.start_date == date(2026, 5, 2)
    assert state.end_date == date(2026, 5, 4)
    assert state.next_start_date == date(2026, 5, 5)
    # 5/5 開始 → 属する月(5月)+2ヶ月後の20日 = 7/20
    assert state.next_end_date == date(2026, 7, 20)
    assert state.latest_night_date == date(2026, 5, 4)
    assert state.latest_night_person_name == "木村"
    assert state.total_entries == 3
    assert people["田中"].day_count == 2
    assert people["田中"].night_count == 0
    assert people["木村"].night_count == 1
    assert people["木村"].last_shift_category == ShiftCategory.NIGHT
