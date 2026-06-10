from datetime import date, timedelta

import pytest

from backend.app.core import config
from backend.app.core.solver import generate_schedule
from backend.app.schemas.ng_entry import NGEntry
from backend.app.schemas.schedule import ScheduleRequest, ScheduleResult
from backend.app.schemas.shift import ShiftCategory, ShiftEntry

# テスト期間: 2026-05-04（月）〜 2026-05-10（日）= 1週間
_WEEK_START = date(2026, 5, 4)   # 月曜
_WEEK_END = date(2026, 5, 10)    # 日曜


def _make_request(**kwargs) -> ScheduleRequest:
    return ScheduleRequest(
        start_date=_WEEK_START,
        end_date=_WEEK_END,
        **kwargs,
    )


def test_night_shift_assigned_for_full_week_from_monday():
    result = generate_schedule(_make_request())
    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    assert len(nights) == 7
    assert {e.date for e in nights} == {_WEEK_START + timedelta(days=i) for i in range(7)}
    assert {e.person_name for e in nights} == {nights[0].person_name}
    assert all(e.shift_index == 1 for e in nights)


def test_short_week_night_interval_relaxed_vs_full_week(monkeypatch: pytest.MonkeyPatch):
    """夜勤が3日分だけの週は、7週空け未満でも割当可（満7日週のときは従来どおり7週空け必須）。"""
    solo = config.MemberConfig(
        name="ソロ夜",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    settings = config.Settings(
        members=[solo],
        schedule=config.ScheduleConfig(
            day_shift_weekdays=[5, 6],
            night_shift_start_weekday=0,
        ),
        constraints=config.ConstraintsConfig(
            day_min_interval=14,
            night_min_interval_weeks=7,
            night_cooldown_days=2,
        ),
    )
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", lambda: settings)
    # 4週前の月曜週の夜勤 → 前月曜週始まりから28日: 満7日週は 28/7=4 < 7 で候補ゼロ。3日分なら 4 < 3 は偽（閾値3）で採択可。
    last_mon = _WEEK_START - timedelta(weeks=4)
    history = [
        ShiftEntry(
            date=last_mon,
            shift_category=ShiftCategory.NIGHT,
            shift_index=1,
            person_name="ソロ夜",
        )
    ]
    end_wed = _WEEK_START + timedelta(days=2)
    r_short = generate_schedule(
        ScheduleRequest(
            start_date=_WEEK_START,
            end_date=end_wed,
            history=history,
            ng_entries=[],
        )
    )
    nights = [e for e in r_short.entries if e.shift_category == ShiftCategory.NIGHT]
    assert len(nights) == 3
    assert not any("夜勤" in w and "スキップ" in w for w in r_short.warnings)

    r_full = generate_schedule(
        ScheduleRequest(
            start_date=_WEEK_START,
            end_date=_WEEK_END,
            history=history,
            ng_entries=[],
        )
    )
    assert any("週の夜勤：候補者なし" in w for w in r_full.warnings)
    gen_nights = [e for e in r_full.entries if e.date >= _WEEK_START and e.shift_category == ShiftCategory.NIGHT]
    assert not gen_nights


def test_night_picks_longest_gap_since_last_night_week(monkeypatch: pytest.MonkeyPatch):
    """候補が複数のとき、前回夜勤週（週始め）から日数が最も空いている人を選ぶ。"""
    m_a = config.MemberConfig(
        name="A遠い",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    m_b = config.MemberConfig(
        name="B近い",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    settings = config.Settings(
        members=[m_a, m_b],
        schedule=config.ScheduleConfig(
            day_shift_weekdays=[5, 6],
            night_shift_start_weekday=0,
        ),
        constraints=config.ConstraintsConfig(
            day_min_interval=14,
            night_min_interval_weeks=7,
            night_cooldown_days=2,
        ),
    )
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", lambda: settings)
    last_b = _WEEK_START - timedelta(weeks=8)  # 8週前の月
    last_a = _WEEK_START - timedelta(weeks=12)  # 12週前
    history = [
        ShiftEntry(
            date=last_a, shift_category=ShiftCategory.NIGHT, shift_index=1, person_name="A遠い"
        ),
        ShiftEntry(
            date=last_b, shift_category=ShiftCategory.NIGHT, shift_index=1, person_name="B近い"
        ),
    ]
    r = generate_schedule(ScheduleRequest(start_date=_WEEK_START, end_date=_WEEK_END, history=history))
    ns = [e for e in r.entries if e.date >= _WEEK_START and e.shift_category == ShiftCategory.NIGHT]
    assert {e.person_name for e in ns} == {"A遠い"}


def test_night_prefers_person_without_prior_weekend_day_shift(monkeypatch: pytest.MonkeyPatch):
    """月曜夜勤の直前土日に日勤していた人は、他候補がいれば夜勤候補の優先度を下げる。"""
    m_a = config.MemberConfig(
        name="A直前日勤",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    m_b = config.MemberConfig(
        name="B未担当",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    settings = config.Settings(
        members=[m_a, m_b],
        schedule=config.ScheduleConfig(
            day_shift_weekdays=[5, 6],
            night_shift_start_weekday=0,
        ),
        constraints=config.ConstraintsConfig(
            day_min_interval=14,
            night_min_interval_weeks=7,
            night_cooldown_days=2,
        ),
    )
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", lambda: settings)
    history = [
        ShiftEntry(
            date=_WEEK_START - timedelta(weeks=12),
            shift_category=ShiftCategory.NIGHT,
            shift_index=1,
            person_name="A直前日勤",
        ),
        ShiftEntry(
            date=_WEEK_START - timedelta(weeks=8),
            shift_category=ShiftCategory.NIGHT,
            shift_index=1,
            person_name="B未担当",
        ),
        ShiftEntry(
            date=_WEEK_START - timedelta(days=2),
            shift_category=ShiftCategory.DAY,
            shift_index=1,
            person_name="A直前日勤",
        ),
    ]

    result = generate_schedule(ScheduleRequest(start_date=_WEEK_START, end_date=_WEEK_END, history=history))
    nights = [e for e in result.entries if e.date >= _WEEK_START and e.shift_category == ShiftCategory.NIGHT]

    assert {e.person_name for e in nights} == {"B未担当"}


def test_night_allows_prior_weekend_day_shift_when_no_other_candidate(monkeypatch: pytest.MonkeyPatch):
    """直前土日に日勤していても、候補不足なら月曜夜勤へ割り当てる。"""
    member = config.MemberConfig(
        name="A直前日勤",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    settings = config.Settings(
        members=[member],
        schedule=config.ScheduleConfig(
            day_shift_weekdays=[5, 6],
            night_shift_start_weekday=0,
        ),
        constraints=config.ConstraintsConfig(
            day_min_interval=14,
            night_min_interval_weeks=7,
            night_cooldown_days=2,
        ),
    )
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", lambda: settings)
    history = [
        ShiftEntry(
            date=_WEEK_START - timedelta(days=1),
            shift_category=ShiftCategory.DAY,
            shift_index=1,
            person_name="A直前日勤",
        )
    ]

    result = generate_schedule(ScheduleRequest(start_date=_WEEK_START, end_date=_WEEK_END, history=history))
    nights = [e for e in result.entries if e.date >= _WEEK_START and e.shift_category == ShiftCategory.NIGHT]

    assert len(nights) == 7
    assert {e.person_name for e in nights} == {"A直前日勤"}


def test_night_shift_short_week_when_later_days_are_ng_holiday():
    """週の途中で期間が終わる・連休で木〜日が全体NGでも、月〜水の夜勤は割り当て可能。"""
    end_wed = _WEEK_START + timedelta(days=2)  # 水曜まで
    holiday = [
        NGEntry(
            person_name=None,
            start_date=_WEEK_START + timedelta(days=3),
            end_date=_WEEK_END,
        ),
    ]
    result = generate_schedule(
        ScheduleRequest(
            start_date=_WEEK_START,
            end_date=end_wed,
            ng_entries=holiday,
            history=[],
        )
    )
    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    assert len(nights) == 3
    assert {e.date for e in nights} == {_WEEK_START + timedelta(days=i) for i in range(3)}
    assert {e.person_name for e in nights} == {nights[0].person_name}
    assert not any("夜勤" in w and "スキップ" in w for w in result.warnings)


def test_night_shift_assigns_before_midweek_global_holiday():
    """水曜から大型連休で夜勤が2日だけでも、その2日を1ブロックとして割り当てる。"""
    week_start = date(2026, 8, 10)  # 月曜
    week_end = week_start + timedelta(days=6)
    holiday_start = week_start + timedelta(days=2)  # 水曜
    result = generate_schedule(
        ScheduleRequest(
            start_date=week_start,
            end_date=week_end,
            ng_entries=[
                NGEntry(
                    person_name=None,
                    start_date=holiday_start,
                    end_date=week_end,
                    reason="大型連休",
                ),
            ],
            history=[],
        )
    )

    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    assert len(nights) == 2
    assert {e.date for e in nights} == {week_start, week_start + timedelta(days=1)}
    assert {e.person_name for e in nights} == {nights[0].person_name}
    assert not any("夜勤" in w and "スキップ" in w for w in result.warnings)


def test_day_shifts_on_saturday_and_sunday():
    result = generate_schedule(_make_request())
    days = [e for e in result.entries if e.shift_category == ShiftCategory.DAY]
    dates = {e.date for e in days}
    sat = date(2026, 5, 9)
    sun = date(2026, 5, 10)
    assert sat in dates
    assert sun in dates


def test_day_shift_has_two_slots_per_day():
    result = generate_schedule(_make_request())
    for d in (date(2026, 5, 9), date(2026, 5, 10)):
        slots = [e for e in result.entries if e.date == d and e.shift_category == ShiftCategory.DAY]
        assert len(slots) == 2
        assert {e.shift_index for e in slots} == {1, 2}


def test_no_duplicate_person_on_same_day():
    result = generate_schedule(_make_request())
    from collections import defaultdict
    by_date: dict = defaultdict(list)
    for e in result.entries:
        by_date[e.date].append(e.person_name)
    for d, names in by_date.items():
        assert len(names) == len(set(names)), f"{d} に同一人物が複数割当"


def test_ng_entry_excludes_person():
    ng = NGEntry(person_name="田中", start_date=_WEEK_START, end_date=_WEEK_END)
    result = generate_schedule(_make_request(ng_entries=[ng]))
    for e in result.entries:
        assert e.person_name != "田中"


def _solo_member_settings() -> config.Settings:
    solo = config.MemberConfig(
        name="ソロ",
        active=True,
        assignable_day1=True,
        assignable_day2=True,
        assignable_night=True,
    )
    return config.Settings(
        members=[solo],
        schedule=config.ScheduleConfig(
            day_shift_weekdays=[5, 6],
            night_shift_start_weekday=0,
        ),
        constraints=config.ConstraintsConfig(
            day_min_interval=14,
            night_min_interval_weeks=7,
            night_cooldown_days=2,
        ),
    )


def test_weekend_ng_does_not_block_night_shift(monkeypatch: pytest.MonkeyPatch):
    """土日NGは昼勤当番への申請。同週の夜勤ブロック（月曜始まり）には影響しない。"""
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", _solo_member_settings)
    sat = date(2026, 5, 9)
    sun = date(2026, 5, 10)
    ng = NGEntry(person_name="ソロ", start_date=sat, end_date=sun)
    result = generate_schedule(_make_request(ng_entries=[ng]))

    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    assert len(nights) == 7
    assert {e.person_name for e in nights} == {"ソロ"}
    assert not any("夜勤" in w and "スキップ" in w for w in result.warnings)
    # 土日の昼勤からは除外される
    assert not any(
        e.shift_category == ShiftCategory.DAY and e.person_name == "ソロ"
        for e in result.entries
    )


def test_monday_ng_blocks_night_shift_block(monkeypatch: pytest.MonkeyPatch):
    """ブロック開始日（月曜）にNGがあれば、その週の夜勤には入れない。"""
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", _solo_member_settings)
    ng = NGEntry(person_name="ソロ", start_date=_WEEK_START, end_date=_WEEK_START)
    result = generate_schedule(_make_request(ng_entries=[ng]))

    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    assert not nights
    assert any("週の夜勤：候補者なし" in w for w in result.warnings)
    # 月曜NGは土日の昼勤には影響しない（土曜は割当可能）
    sat_days = [
        e for e in result.entries
        if e.shift_category == ShiftCategory.DAY and e.date == date(2026, 5, 9)
    ]
    assert any(e.person_name == "ソロ" for e in sat_days)


def test_day_min_interval_respected():
    sat = date(2026, 5, 9)
    # 前週土曜（7日前）に日勤した人を履歴に入れる → 14日未満なので除外されるはず
    prev_sat = sat - timedelta(days=7)
    history = [ShiftEntry(date=prev_sat, shift_category=ShiftCategory.DAY, shift_index=1, person_name="丸岡")]
    result = generate_schedule(_make_request(history=history))
    day_entries = [e for e in result.entries if e.shift_category == ShiftCategory.DAY]
    # 丸岡は14日間隔未満のため割り当てられていないはず
    assert not any(e.person_name == "丸岡" for e in day_entries)


def test_night_cooldown_prevents_day_shift():
    # 月曜に夜勤した人は同週土日の日勤に入れない（cooldown_days=2 なので月〜水は除外）
    result = generate_schedule(_make_request())
    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    if not nights:
        pytest.skip("夜勤割当なし")
    night_person = nights[0].person_name
    night_date = nights[0].date
    day_entries = [
        e for e in result.entries
        if e.shift_category == ShiftCategory.DAY and e.person_name == night_person
    ]
    for e in day_entries:
        assert (e.date - night_date).days > 2, f"{night_person} がクールダウン期間中に日勤割当"


def test_result_is_schedule_result_instance():
    result = generate_schedule(_make_request())
    assert isinstance(result, ScheduleResult)


def test_warnings_field_exists():
    result = generate_schedule(_make_request())
    assert isinstance(result.warnings, list)


def test_result_includes_next_history_state():
    history = [
        ShiftEntry(date=date(2026, 4, 25), shift_category=ShiftCategory.DAY, shift_index=1, person_name="田中"),
    ]
    result = generate_schedule(_make_request(history=history))

    assert len(result.next_history) > len(history)
    assert result.reference_history_state.total_entries == len(history)
    assert result.history_state.total_entries == len(result.next_history)
    assert any(person.person_name == "田中" for person in result.history_state.people)


def test_existing_history_slots_in_range_are_fixed():
    existing = [
        ShiftEntry(date=_WEEK_START, shift_category=ShiftCategory.NIGHT, shift_index=1, person_name="楮本"),
        ShiftEntry(date=date(2026, 5, 9), shift_category=ShiftCategory.DAY, shift_index=1, person_name="田中"),
    ]
    result = generate_schedule(_make_request(history=existing))

    matching_night = [
        entry for entry in result.entries
        if entry.date == _WEEK_START and entry.shift_category == ShiftCategory.NIGHT and entry.shift_index == 1
    ]
    matching_day = [
        entry for entry in result.entries
        if entry.date == date(2026, 5, 9) and entry.shift_category == ShiftCategory.DAY and entry.shift_index == 1
    ]

    assert len(matching_night) == 1
    assert matching_night[0].person_name == "楮本"
    assert len(matching_day) == 1
    assert matching_day[0].person_name == "田中"


def test_next_weekend_day_shifts_after_night_week_exclude_that_person():
    history = [
        ShiftEntry(
            date=date(2026, 5, 3),
            shift_category=ShiftCategory.NIGHT,
            shift_index=1,
            person_name="楮本",
        )
    ]
    result = generate_schedule(_make_request(history=history))

    weekend_days_after_night = [
        entry for entry in result.entries
        if entry.date in {date(2026, 5, 9), date(2026, 5, 10)}
        and entry.shift_category == ShiftCategory.DAY
    ]

    assert weekend_days_after_night
    assert all(entry.person_name != "楮本" for entry in weekend_days_after_night)


def test_two_week_range():
    result = generate_schedule(ScheduleRequest(
        start_date=date(2026, 5, 4),
        end_date=date(2026, 5, 17),
    ))
    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    # 2週分なので夜勤は14件（月曜開始の7日間×2週）
    assert len(nights) == 14
    days = [e for e in result.entries if e.shift_category == ShiftCategory.DAY]
    # 土日×2週×2スロット = 8件
    assert len(days) == 8


def test_sunday_period_start_carries_week_night_from_history():
    """期間が週の最終日（日）だけのとき、直前までの夜勤週を履歴から引き継ぐ。"""
    anchor = date(2026, 6, 15)  # 月
    history = [
        ShiftEntry(
            date=anchor + timedelta(days=i),
            shift_category=ShiftCategory.NIGHT,
            shift_index=1,
            person_name="高橋拓",
        )
        for i in range(6)
    ]
    sunday = date(2026, 6, 21)
    result = generate_schedule(ScheduleRequest(
        start_date=sunday,
        end_date=sunday,
        history=history,
        ng_entries=[],
    ))
    sun_nights = [
        e for e in result.entries
        if e.date == sunday and e.shift_category == ShiftCategory.NIGHT
    ]
    assert len(sun_nights) == 1
    assert sun_nights[0].person_name == "高橋拓"


def _five_member_settings() -> config.Settings:
    members = [
        config.MemberConfig(
            name=n,
            active=True,
            assignable_day1=True,
            assignable_day2=True,
            assignable_night=True,
        )
        for n in ["A川", "B田", "C山", "D野", "E原"]
    ]
    return config.Settings(
        members=members,
        schedule=config.ScheduleConfig(
            day_shift_weekdays=[5, 6],
            night_shift_start_weekday=0,
        ),
        constraints=config.ConstraintsConfig(
            day_min_interval=14,
            night_min_interval_weeks=7,
            night_cooldown_days=2,
        ),
    )


def test_pinned_day_entry_is_kept(monkeypatch: pytest.MonkeyPatch):
    """手動確定した日勤枠はソルバに上書きされず、そのスロットは1件のみ。"""
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", _five_member_settings)
    sat = _WEEK_START + timedelta(days=5)
    pinned = ShiftEntry(
        date=sat, shift_category=ShiftCategory.DAY, shift_index=1, person_name="D野"
    )
    result = generate_schedule(_make_request(pinned_entries=[pinned]))
    slot = [
        e for e in result.entries
        if e.date == sat and e.shift_category == ShiftCategory.DAY and e.shift_index == 1
    ]
    assert len(slot) == 1
    assert slot[0].person_name == "D野"
    # 同日の2番手や夜勤に同一人物が重複しない
    same_day_others = [
        e for e in result.entries
        if e.date == sat and not (e.shift_category == ShiftCategory.DAY and e.shift_index == 1)
    ]
    assert all(e.person_name != "D野" for e in same_day_others)


def test_pinned_night_entry_carries_to_whole_week(monkeypatch: pytest.MonkeyPatch):
    """週の一部だけ夜勤を手動確定しても、同じ担当者が週全体に引き継がれる。"""
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", _five_member_settings)
    pinned = ShiftEntry(
        date=_WEEK_START, shift_category=ShiftCategory.NIGHT, shift_index=1, person_name="E原"
    )
    result = generate_schedule(_make_request(pinned_entries=[pinned]))
    nights = [e for e in result.entries if e.shift_category == ShiftCategory.NIGHT]
    assert len(nights) == 7
    assert {e.person_name for e in nights} == {"E原"}


def test_pinned_overrides_history_same_slot(monkeypatch: pytest.MonkeyPatch):
    """履歴と同一スロットに手動確定がある場合、手動確定が優先され next_history にも反映。"""
    import backend.app.core.solver as solver_mod

    monkeypatch.setattr(solver_mod, "load_settings", _five_member_settings)
    sat = _WEEK_START + timedelta(days=5)
    hist_entry = ShiftEntry(
        date=sat, shift_category=ShiftCategory.DAY, shift_index=1, person_name="A川"
    )
    pinned = ShiftEntry(
        date=sat, shift_category=ShiftCategory.DAY, shift_index=1, person_name="B田"
    )
    result = generate_schedule(
        _make_request(history=[hist_entry], pinned_entries=[pinned])
    )
    slot = [
        e for e in result.entries
        if e.date == sat and e.shift_category == ShiftCategory.DAY and e.shift_index == 1
    ]
    assert len(slot) == 1
    assert slot[0].person_name == "B田"
    next_slot = [
        e for e in result.next_history
        if e.date == sat and e.shift_category == ShiftCategory.DAY and e.shift_index == 1
    ]
    assert len(next_slot) == 1
    assert next_slot[0].person_name == "B田"
