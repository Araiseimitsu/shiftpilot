from datetime import date
from pydantic import BaseModel, Field
from backend.app.schemas.history import HistoryState
from backend.app.schemas.shift import ShiftEntry
from backend.app.schemas.ng_entry import NGEntry


class ScheduleRequest(BaseModel):
    start_date: date
    end_date: date
    ng_entries: list[NGEntry] = Field(default_factory=list)
    history: list[ShiftEntry] = Field(default_factory=list)


class ScheduleResult(BaseModel):
    entries: list[ShiftEntry]
    warnings: list[str] = Field(default_factory=list)
    next_history: list[ShiftEntry] = Field(default_factory=list)
    reference_history_state: HistoryState = Field(default_factory=HistoryState)
    history_state: HistoryState = Field(default_factory=HistoryState)
