from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel

_PROJECT_ROOT = Path(__file__).parents[3]
_SETTINGS_PATH = _PROJECT_ROOT / "config" / "settings.yaml"


class MemberConfig(BaseModel):
    name: str
    active: bool = True
    assignable_day1: bool = True
    assignable_day2: bool = True
    assignable_night: bool = True


class ScheduleConfig(BaseModel):
    day_shift_weekdays: list[int] = [5, 6]
    night_shift_start_weekday: int = 0


class ConstraintsConfig(BaseModel):
    day_min_interval: int = 14
    night_min_interval_weeks: int = 7
    night_cooldown_days: int = 2


class Settings(BaseModel):
    members: list[MemberConfig]
    schedule: ScheduleConfig
    constraints: ConstraintsConfig


def load_settings(path: Path = _SETTINGS_PATH) -> Settings:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Settings(**raw)
