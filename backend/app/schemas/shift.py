from datetime import date
from enum import Enum
from pydantic import BaseModel


class ShiftCategory(str, Enum):
    DAY = "Day"
    NIGHT = "Night"
    MANUAL = "Manual"


class ShiftEntry(BaseModel):
    date: date
    shift_category: ShiftCategory
    shift_index: int  # Day: 1 or 2 / Night: 1 のみ
    person_name: str
