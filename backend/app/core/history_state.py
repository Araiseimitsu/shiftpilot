from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

from backend.app.schemas.history import HistoryState, PersonHistoryState
from backend.app.schemas.shift import ShiftCategory, ShiftEntry


def _add_calendar_months(year: int, month: int, delta: int) -> tuple[int, int]:
    """month は 1–12。delta ヶ月後の (年, 月) を返す。"""
    m0 = month - 1 + delta
    y = year + m0 // 12
    m = m0 % 12 + 1
    return y, m


def next_assignment_period_end(period_start: date) -> date:
    """当番作成の終了日: 期間開始日の属する月から数えて2ヶ月後の20日（21日〜翌々月20日の運用）。"""
    y, m = _add_calendar_months(period_start.year, period_start.month, 2)
    return date(y, m, 20)


def normalize_entries(entries: Iterable[ShiftEntry]) -> list[ShiftEntry]:
    """同じ日付・区分・番手の割当は後勝ちで1件に正規化する。"""
    by_slot: dict[tuple[date, ShiftCategory, int], ShiftEntry] = {}
    for entry in entries:
        by_slot[(entry.date, entry.shift_category, entry.shift_index)] = entry
    return sorted(
        by_slot.values(),
        key=lambda e: (e.date, e.shift_category.value, e.shift_index),
    )


def build_history_state(entries: Iterable[ShiftEntry]) -> HistoryState:
    normalized = normalize_entries(entries)
    if not normalized:
        return HistoryState()

    end_date = max(entry.date for entry in normalized)
    latest_night = max(
        (entry for entry in normalized if entry.shift_category == ShiftCategory.NIGHT),
        key=lambda entry: entry.date,
        default=None,
    )
    by_person: dict[str, list[ShiftEntry]] = defaultdict(list)
    for entry in normalized:
        by_person[entry.person_name].append(entry)

    people: list[PersonHistoryState] = []
    for person_name, person_entries in sorted(by_person.items()):
        ordered = sorted(person_entries, key=lambda e: (e.date, e.shift_category.value, e.shift_index))
        last_entry = ordered[-1]
        work_dates = {entry.date for entry in ordered}
        consecutive = 0
        cursor = end_date
        while cursor in work_dates:
            consecutive += 1
            cursor -= timedelta(days=1)

        people.append(
            PersonHistoryState(
                person_name=person_name,
                total_count=len(ordered),
                day_count=sum(1 for entry in ordered if entry.shift_category == ShiftCategory.DAY),
                night_count=sum(1 for entry in ordered if entry.shift_category == ShiftCategory.NIGHT),
                last_shift_date=last_entry.date,
                last_shift_category=last_entry.shift_category,
                consecutive_work_days_at_end=consecutive,
            )
        )

    next_start = end_date + timedelta(days=1)
    return HistoryState(
        entries=normalized,
        start_date=min(entry.date for entry in normalized),
        end_date=end_date,
        next_start_date=next_start,
        next_end_date=next_assignment_period_end(next_start),
        latest_night_date=latest_night.date if latest_night else None,
        latest_night_person_name=latest_night.person_name if latest_night else None,
        total_entries=len(normalized),
        people=people,
    )
