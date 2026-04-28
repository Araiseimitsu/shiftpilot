"""手入力用スタッフ名一覧の永続化（PyInstaller では exe と同じフォルダの JSON）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.project_root import project_root

router = APIRouter(prefix="/manual_staff", tags=["manual_staff"])


class ManualStaffEntry(BaseModel):
    name: str = Field(min_length=1)


def _manual_staff_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "manual_staff.json"
    return project_root() / ".docs" / "manual_staff.json"


def _load() -> list[ManualStaffEntry]:
    path = _manual_staff_file()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=422,
            detail=f"manual_staff.json の形式が不正です: {e}",
        ) from e
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="manual_staff.json は JSON 配列である必要があります")
    out: list[ManualStaffEntry] = []
    for i, row in enumerate(raw):
        try:
            out.append(ManualStaffEntry.model_validate(row))
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"manual_staff.json の {i} 件目が不正です: {e}",
            ) from e
    return out


def _save(items: list[ManualStaffEntry]) -> None:
    path = _manual_staff_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([m.model_dump() for m in items], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@router.get("", response_model=list[ManualStaffEntry])
def get_manual_staff() -> list[ManualStaffEntry]:
    return _load()


@router.put("", response_model=list[ManualStaffEntry])
def put_manual_staff(items: list[ManualStaffEntry]) -> list[ManualStaffEntry]:
    """手入力スタッフ一覧をまるごと保存する。"""
    _save(items)
    return items
