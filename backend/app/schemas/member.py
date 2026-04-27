from pydantic import BaseModel


class Member(BaseModel):
    name: str
    active: bool
    assignable_day1: bool
    assignable_day2: bool
    assignable_night: bool
