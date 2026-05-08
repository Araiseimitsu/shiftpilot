from datetime import date, timedelta

from backend.app.core.config import load_settings
from backend.app.core.history_state import build_history_state, normalize_entries
from backend.app.schemas.ng_entry import NGEntry
from backend.app.schemas.schedule import ScheduleRequest, ScheduleResult
from backend.app.schemas.shift import ShiftCategory, ShiftEntry


def _is_ng(name: str, d: date, ng_entries: list[NGEntry]) -> bool:
    for ng in ng_entries:
        if ng.start_date <= d <= ng.end_date:
            if ng.person_name is None or ng.person_name == name:
                return True
    return False


def _is_global_ng(d: date, ng_entries: list[NGEntry]) -> bool:
    return any(
        ng.person_name is None and ng.start_date <= d <= ng.end_date
        for ng in ng_entries
    )


def _last_shift_date(name: str, history: list[ShiftEntry], category: ShiftCategory | None = None) -> date | None:
    matches = [
        e.date for e in history
        if e.person_name == name and (category is None or e.shift_category == category)
    ]
    return max(matches) if matches else None


def _slot_shift_count(
    name: str,
    history: list[ShiftEntry],
    category: ShiftCategory,
    shift_index: int | None = None,
) -> int:
    return sum(
        1 for e in history
        if (
            e.person_name == name
            and e.shift_category == category
            and (shift_index is None or e.shift_index == shift_index)
        )
    )


def _last_shift_person(
    history: list[ShiftEntry],
    category: ShiftCategory,
    shift_index: int | None = None,
) -> str | None:
    matches = [
        e for e in history
        if e.shift_category == category and (shift_index is None or e.shift_index == shift_index)
    ]
    if not matches:
        return None
    latest = max(matches, key=lambda e: (e.date, e.shift_index))
    return latest.person_name


def _rotation_distance(name: str, pool: list[str], last_person: str | None) -> int:
    if not pool:
        return 0
    if last_person not in pool:
        return pool.index(name)
    last_index = pool.index(last_person)
    return (pool.index(name) - last_index - 1) % len(pool)


def _week_start(d: date, start_weekday: int) -> date:
    return d - timedelta(days=(d.weekday() - start_weekday) % 7)


def _last_night_week_start(name: str, history: list[ShiftEntry], start_weekday: int) -> date | None:
    matches = [
        _week_start(e.date, start_weekday)
        for e in history
        if e.person_name == name and e.shift_category == ShiftCategory.NIGHT
    ]
    return max(matches) if matches else None


def _night_block_count(name: str, history: list[ShiftEntry], start_weekday: int) -> int:
    return len({
        _week_start(e.date, start_weekday)
        for e in history
        if e.person_name == name and e.shift_category == ShiftCategory.NIGHT
    })


def _night_candidate_sort_key(
    name: str,
    pool: list[str],
    history: list[ShiftEntry],
    current_week_start: date,
    night_start_weekday: int,
    prior_weekend_day_names: set[str] | None = None,
) -> tuple[int, int, int, str]:
    """候補が複数のとき: 前回夜勤週（週始め基準）から最も日数が空いている人を最優先、同率で従来の回転・回数。名前で安定化。"""
    last_ws = _last_night_week_start(name, history, night_start_weekday)
    gap_days = (current_week_start - last_ws).days if last_ws is not None else 10_000
    last_person = _last_shift_person(history, ShiftCategory.NIGHT, 1)
    rot = _rotation_distance(name, pool, last_person)
    count = _night_block_count(name, history, night_start_weekday)
    prior_weekend_penalty = 1 if prior_weekend_day_names and name in prior_weekend_day_names else 0
    return (prior_weekend_penalty, -gap_days, rot, count, name)


def _prior_weekend_day_shift_names(
    history: list[ShiftEntry],
    current_week_start: date,
    day_shift_weekdays: list[int],
) -> set[str]:
    """夜勤開始直前の土日など、日勤対象曜日に入っていた担当者を返す。"""
    return {
        e.person_name
        for e in history
        if (
            e.shift_category == ShiftCategory.DAY
            and e.date < current_week_start
            and (current_week_start - e.date).days <= 2
            and e.date.weekday() in day_shift_weekdays
        )
    }


def _day_candidate_sort_key(
    name: str,
    pool: list[str],
    history: list[ShiftEntry],
    current: date,
    shift_index: int,
) -> tuple[int, int, int, str]:
    """前回の日勤日から最も日数が空いている人を最優先、同率で1番/2番それぞれの回転とスロット回数。名前で安定化。"""
    last_day = _last_shift_date(name, history, ShiftCategory.DAY)
    gap_days = (current - last_day).days if last_day is not None else 10_000
    last_person = _last_shift_person(history, ShiftCategory.DAY, shift_index)
    rot = _rotation_distance(name, pool, last_person)
    count = _slot_shift_count(name, history, ShiftCategory.DAY, shift_index)
    return (-gap_days, rot, count, name)


def _carry_forward_week_nights_from_history(
    *,
    start_date: date,
    end_date: date,
    night_start_weekday: int,
    history: list[ShiftEntry],
    result_entries: list[ShiftEntry],
    generated_entries: list[ShiftEntry],
) -> list[ShiftEntry]:
    """期間開始が週の途中のとき、履歴に同一週（月曜基準）の夜勤があれば担当者を週末まで引き継ぐ。

    夜勤ブロックは「週の開始曜日」（設定の night_shift_start_weekday）にだけ走るため、
    期間が日曜から始まるなどすると最終日の夜勤だけ空になる。CSV 最終日まで週が続いている場合はここで埋める。
    """
    anchor = _week_start(start_date, night_start_weekday)
    if start_date <= anchor:
        return []
    week_end = anchor + timedelta(days=6)
    prior_nights = [
        e
        for e in history
        if e.shift_category == ShiftCategory.NIGHT
        and anchor <= e.date < start_date
    ]
    if not prior_nights:
        return []
    person = max(prior_nights, key=lambda e: (e.date, e.shift_index)).person_name
    added: list[ShiftEntry] = []
    d = start_date
    last = min(week_end, end_date)
    while d <= last:
        occupied = any(
            e.date == d
            and e.shift_category == ShiftCategory.NIGHT
            and e.shift_index == 1
            for e in result_entries
        )
        if not occupied:
            entry = ShiftEntry(
                date=d,
                shift_category=ShiftCategory.NIGHT,
                shift_index=1,
                person_name=person,
            )
            result_entries.append(entry)
            generated_entries.append(entry)
            added.append(entry)
        d += timedelta(days=1)
    return added


def _is_next_day_shift_weekend_after_last_night(
    name: str,
    current: date,
    history: list[ShiftEntry],
    day_shift_weekdays: list[int],
) -> bool:
    last_night = _last_shift_date(name, history, ShiftCategory.NIGHT)
    if last_night is None or current <= last_night:
        return False

    first_day_shift_after_night: date | None = None
    cursor = last_night + timedelta(days=1)
    while cursor <= current + timedelta(days=6):
        if cursor.weekday() in day_shift_weekdays:
            first_day_shift_after_night = cursor
            break
        cursor += timedelta(days=1)

    if first_day_shift_after_night is None:
        return False

    protected_week_start = _week_start(first_day_shift_after_night, min(day_shift_weekdays))
    protected_week_end = protected_week_start + timedelta(days=6)
    return (
        protected_week_start <= current <= protected_week_end
        and current.weekday() in day_shift_weekdays
    )


def generate_schedule(request: ScheduleRequest) -> ScheduleResult:
    settings = load_settings()
    cfg = settings.constraints
    sched_cfg = settings.schedule

    # スロット別の候補者リスト
    pool_day1 = [m.name for m in settings.members if m.active and m.assignable_day1]
    pool_day2 = [m.name for m in settings.members if m.active and m.assignable_day2]
    pool_night = [m.name for m in settings.members if m.active and m.assignable_night]

    ng_entries = request.ng_entries
    history: list[ShiftEntry] = list(request.history)
    reference_history_state = build_history_state(history)
    warnings: list[str] = []
    fixed_entries = [
        entry
        for entry in history
        if request.start_date <= entry.date <= request.end_date
    ]
    generated_entries: list[ShiftEntry] = []
    result_entries: list[ShiftEntry] = list(fixed_entries)

    carried_nights = _carry_forward_week_nights_from_history(
        start_date=request.start_date,
        end_date=request.end_date,
        night_start_weekday=sched_cfg.night_shift_start_weekday,
        history=history,
        result_entries=result_entries,
        generated_entries=generated_entries,
    )
    if carried_nights:
        history = history + carried_nights

    def is_occupied(d: date, category: ShiftCategory, index: int) -> bool:
        return any(
            entry.date == d and entry.shift_category == category and entry.shift_index == index
            for entry in result_entries
        )

    current = request.start_date
    while current <= request.end_date:
        weekday = current.weekday()  # 0=月, 5=土, 6=日

        # --- 夜勤（月曜始まり週1名）---
        if weekday == sched_cfg.night_shift_start_weekday:
            sat = current + timedelta(days=(5 - weekday) % 7)
            sun = sat + timedelta(days=1)
            prior_weekend_day_names = _prior_weekend_day_shift_names(
                history,
                current,
                sched_cfg.day_shift_weekdays,
            )
            week_dates = [
                current + timedelta(days=d)
                for d in range(7)
                if current + timedelta(days=d) <= request.end_date
            ]
            open_night_dates = [
                d for d in week_dates
                if not is_occupied(d, ShiftCategory.NIGHT, 1)
                and not _is_global_ng(d, ng_entries)
            ]
            if not open_night_dates:
                current += timedelta(days=1)
                continue
            # 休業日を除いた夜勤が7日分に満たない週は、7週空け（night_min_interval_weeks）のままだと全員
            # (current - last_night) / 7 < 7 で落ち、候補ゼロになりやすい。割当日数/7に比例して必要間隔を下げる。
            night_block_ratio = min(len(open_night_dates) / 7.0, 1.0)
            required_night_interval_weeks = cfg.night_min_interval_weeks * night_block_ratio
            candidates = []
            for name in pool_night:
                # 7日分そろわない週（大型連休で出力期間が短い等）は、割当対象日のみでNGを見る
                if any(_is_ng(name, d, ng_entries) for d in open_night_dates):
                    continue
                if any(e.date in (sat, sun) and e.person_name == name for e in result_entries):
                    continue
                last_night = _last_night_week_start(name, history, sched_cfg.night_shift_start_weekday)
                if last_night and (current - last_night).days / 7 < required_night_interval_weeks:
                    continue
                candidates.append(name)

            if not candidates:
                warnings.append(f"{current.isoformat()} 週の夜勤：候補者なし（スキップ）")
            else:
                candidates.sort(
                    key=lambda n: _night_candidate_sort_key(
                        n,
                        pool_night,
                        history,
                        current,
                        sched_cfg.night_shift_start_weekday,
                        prior_weekend_day_names,
                    )
                )
                chosen = candidates[0]
                week_entries = [
                    ShiftEntry(date=d, shift_category=ShiftCategory.NIGHT, shift_index=1, person_name=chosen)
                    for d in open_night_dates
                ]
                result_entries.extend(week_entries)
                generated_entries.extend(week_entries)
                history = history + week_entries

        # --- 日勤（土日のみ、1番手・2番手）---
        if weekday in sched_cfg.day_shift_weekdays:
            night_today = {e.person_name for e in result_entries if e.date == current and e.shift_category == ShiftCategory.NIGHT}
            assigned_today = [
                e.person_name
                for e in result_entries
                if e.date == current and e.shift_category == ShiftCategory.DAY
            ]

            for slot_index, pool in ((1, pool_day1), (2, pool_day2)):
                if is_occupied(current, ShiftCategory.DAY, slot_index):
                    continue
                candidates = []
                for name in pool:
                    if name in night_today:
                        continue
                    if name in assigned_today:
                        continue
                    if _is_ng(name, current, ng_entries):
                        continue
                    last_day = _last_shift_date(name, history, ShiftCategory.DAY)
                    if last_day and (current - last_day).days < cfg.day_min_interval:
                        continue
                    last_night = _last_shift_date(name, history, ShiftCategory.NIGHT)
                    if last_night and (current - last_night).days <= cfg.night_cooldown_days:
                        continue
                    if _is_next_day_shift_weekend_after_last_night(name, current, history, sched_cfg.day_shift_weekdays):
                        continue
                    candidates.append(name)

                if not candidates:
                    warnings.append(f"{current.isoformat()} 日勤{slot_index}番手：候補者なし（スキップ）")
                else:
                    candidates.sort(
                        key=lambda n: _day_candidate_sort_key(n, pool, history, current, slot_index)
                    )
                    chosen = candidates[0]
                    entry = ShiftEntry(date=current, shift_category=ShiftCategory.DAY, shift_index=slot_index, person_name=chosen)
                    result_entries.append(entry)
                    generated_entries.append(entry)
                    assigned_today.append(chosen)
                    history = history + [entry]

        current += timedelta(days=1)

    next_history = normalize_entries([*request.history, *generated_entries])
    return ScheduleResult(
        entries=result_entries,
        warnings=warnings,
        next_history=next_history,
        reference_history_state=reference_history_state,
        history_state=build_history_state(next_history),
    )
