from fastapi import APIRouter
from pydantic import BaseModel
from datetime import date
from backend.app.schemas.ng_entry import NGEntry
from backend.app.core.ng_parser import parse_ng_text

router = APIRouter(prefix="/ng_entries", tags=["ng_entries"])

# インメモリストア（M3 でファイル永続化に変更予定）
_store: list[NGEntry] = []


@router.get("", response_model=list[NGEntry])
def list_ng_entries() -> list[NGEntry]:
    return list(_store)


@router.post("", response_model=NGEntry, status_code=201)
def create_ng_entry(entry: NGEntry) -> NGEntry:
    _store.append(entry)
    return entry


@router.delete("/{index}", status_code=204)
def delete_ng_entry(index: int) -> None:
    if 0 <= index < len(_store):
        _store.pop(index)


# --- 一括貼り付け登録 ---

class BulkNGParseRequest(BaseModel):
    text: str
    default_year: int | None = None
    shift_type: str = ""  # "day" | "night" | ""


class BulkNGParseItem(BaseModel):
    person_name: str
    dates: list[date]


class BulkNGParseResponse(BaseModel):
    items: list[BulkNGParseItem]


class BulkNGRegisterRequest(BaseModel):
    items: list[BulkNGParseItem]
    shift_type: str = ""
    reason_template: str = "{shift_type}NG"


@router.post("/bulk_parse", response_model=BulkNGParseResponse)
def bulk_parse_ng(req: BulkNGParseRequest) -> BulkNGParseResponse:
    parsed = parse_ng_text(req.text, default_year=req.default_year)
    return BulkNGParseResponse(
        items=[
            BulkNGParseItem(person_name=p.person_name, dates=p.dates)
            for p in parsed
        ]
    )


@router.post("/bulk", status_code=201)
def bulk_register_ng(req: BulkNGRegisterRequest) -> dict[str, int]:
    shift_label = ""
    if req.shift_type == "day":
        shift_label = "日勤"
    elif req.shift_type == "night":
        shift_label = "夜勤"

    reason = req.reason_template.format(shift_type=shift_label)

    count = 0
    for item in req.items:
        for d in item.dates:
            entry = NGEntry(
                person_name=item.person_name,
                start_date=d,
                end_date=d,
                reason=reason,
            )
            _store.append(entry)
            count += 1

    return {"registered": count}
