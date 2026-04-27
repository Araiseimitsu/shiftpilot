from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml

from backend.app.core.config import load_settings, _SETTINGS_PATH
from backend.app.schemas.member import Member

router = APIRouter(prefix="/members", tags=["members"])


class MemberFlagsUpdate(BaseModel):
    assignable_day1: bool
    assignable_day2: bool
    assignable_night: bool


@router.get("", response_model=list[Member])
def list_members() -> list[Member]:
    settings = load_settings()
    return [
        Member(
            name=m.name,
            active=m.active,
            assignable_day1=m.assignable_day1,
            assignable_day2=m.assignable_day2,
            assignable_night=m.assignable_night,
        )
        for m in settings.members
    ]


@router.patch("/{name}/flags", response_model=Member)
def update_member_flags(name: str, update: MemberFlagsUpdate) -> Member:
    raw = yaml.safe_load(_SETTINGS_PATH.read_text(encoding="utf-8"))
    found = next((m for m in raw["members"] if m["name"] == name), None)
    if not found:
        raise HTTPException(status_code=404, detail=f"{name} が見つかりません")
    found["assignable_day1"] = update.assignable_day1
    found["assignable_day2"] = update.assignable_day2
    found["assignable_night"] = update.assignable_night
    _SETTINGS_PATH.write_text(
        yaml.dump(raw, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    settings = load_settings()
    m = next(x for x in settings.members if x.name == name)
    return Member(
        name=m.name,
        active=m.active,
        assignable_day1=m.assignable_day1,
        assignable_day2=m.assignable_day2,
        assignable_night=m.assignable_night,
    )
