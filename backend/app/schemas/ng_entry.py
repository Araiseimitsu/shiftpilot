from datetime import date
from pydantic import BaseModel


class NGEntry(BaseModel):
    person_name: str | None = None  # None = 全体NG
    start_date: date
    end_date: date
    reason: str = ""
