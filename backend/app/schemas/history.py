from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.shift import ShiftCategory, ShiftEntry


class PersonHistoryState(BaseModel):
    person_name: str
    total_count: int = 0
    day_count: int = 0
    night_count: int = 0
    last_shift_date: date | None = None
    last_shift_category: ShiftCategory | None = None
    consecutive_work_days_at_end: int = 0


class HistoryState(BaseModel):
    entries: list[ShiftEntry] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    next_start_date: date | None = None
    next_end_date: date | None = None
    latest_night_date: date | None = None
    latest_night_person_name: str | None = None
    total_entries: int = 0
    people: list[PersonHistoryState] = Field(default_factory=list)


class HistorySourceInfo(BaseModel):
    """どの履歴 CSV がメモリに載っているか（デフォルト読込 / アップロード / 未配置）。"""

    kind: Literal["default", "upload", "empty"] = "empty"
    label: str = ""
    row_count: int = 0
    default_path: str = ".docs/previous_data.csv"
