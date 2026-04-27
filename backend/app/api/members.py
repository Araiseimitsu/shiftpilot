from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml

from backend.app.core.config import load_settings, _SETTINGS_PATH
from backend.app.schemas.member import Member

router = APIRouter(prefix="/members", tags=["members"])


def _load_raw() -> dict[str, Any]:
    return yaml.safe_load(_SETTINGS_PATH.read_text(encoding="utf-8"))


def _save_raw(raw: dict[str, Any]) -> None:
    _SETTINGS_PATH.write_text(
        yaml.dump(raw, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


class MemberFlagsUpdate(BaseModel):
    assignable_day1: bool
    assignable_day2: bool
    assignable_night: bool


class MemberCreate(BaseModel):
    name: str
    assignable_day1: bool = True
    assignable_day2: bool = True
    assignable_night: bool = True


@router.get("", response_model=list[Member])
def list_members() -> list[Member]:
    settings = load_settings()
    return [Member.model_validate(m.model_dump()) for m in settings.members]


@router.post("", response_model=Member, status_code=201)
def create_member(body: MemberCreate) -> Member:
    raw = _load_raw()
    members = raw.get("members", [])
    if any(m["name"] == body.name for m in members):
        raise HTTPException(status_code=409, detail=f"{body.name} は既に存在します")
    new_member = {
        "name": body.name,
        "active": True,
        "assignable_day1": body.assignable_day1,
        "assignable_day2": body.assignable_day2,
        "assignable_night": body.assignable_night,
    }
    members.append(new_member)
    raw["members"] = members
    _save_raw(raw)
    return Member(**new_member)


@router.delete("/{name}", status_code=204)
def delete_member(name: str) -> None:
    raw = _load_raw()
    members = raw.get("members", [])
    filtered = [m for m in members if m["name"] != name]
    if len(filtered) == len(members):
        raise HTTPException(status_code=404, detail=f"{name} が見つかりません")
    raw["members"] = filtered
    _save_raw(raw)


@router.patch("/{name}/flags", response_model=Member)
def update_member_flags(name: str, update: MemberFlagsUpdate) -> Member:
    raw = _load_raw()
    found = next((m for m in raw["members"] if m["name"] == name), None)
    if not found:
        raise HTTPException(status_code=404, detail=f"{name} が見つかりません")
    found["assignable_day1"] = update.assignable_day1
    found["assignable_day2"] = update.assignable_day2
    found["assignable_night"] = update.assignable_night
    _save_raw(raw)
    settings = load_settings()
    m = next(x for x in settings.members if x.name == name)
    return Member.model_validate(m.model_dump())
