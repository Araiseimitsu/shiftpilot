from fastapi import APIRouter
from backend.app.schemas.ng_entry import NGEntry

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
