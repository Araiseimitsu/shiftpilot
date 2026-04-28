from pathlib import Path
import sys
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response

from backend.app.core.csv_io import dump_csv, load_csv, ENCODING
from backend.app.core.history_state import build_history_state, normalize_entries
from backend.app.project_root import project_root
from backend.app.schemas.history import HistorySourceInfo, HistoryState
from backend.app.schemas.shift import ShiftEntry

router = APIRouter(prefix="/history", tags=["history"])


def _resolved_default_csv() -> tuple[str, Path]:
    """既定履歴CSVの(API表示用説明文字列, 実パス)。
    PyInstaller ビルド時は .exe と同じフォルダの previous_data.csv を参照する。
    """
    if getattr(sys, "frozen", False):
        p = Path(sys.executable).resolve().parent / "previous_data.csv"
        return ("previous_data.csv（実行ファイルと同じフォルダ）", p)
    repo = project_root()
    p = repo / ".docs" / "previous_data.csv"
    return (".docs/previous_data.csv", p)


_DEFAULT_REL, _DEFAULT_CSV = _resolved_default_csv()

# アップロード済みデータのインメモリキャッシュ
_history: list[ShiftEntry] = []
_loaded = False
_source_kind: str = "empty"
_source_label: str = ""


def load_default_csv() -> None:
    """既定CSVがあれば読み込む（開発時: .docs/、PyInstaller: exe と同じフォルダ）。起動時の lifespan から呼ぶ。"""
    global _loaded, _source_kind, _source_label
    if not _loaded and _DEFAULT_CSV.exists():
        _history.extend(load_csv(_DEFAULT_CSV))
        _loaded = True
        _source_kind = "default"
        _source_label = _DEFAULT_REL


def _ensure_loaded() -> None:
    load_default_csv()


@router.get("", response_model=list[ShiftEntry])
def list_history() -> list[ShiftEntry]:
    _ensure_loaded()
    return list(_history)


@router.get("/state", response_model=HistoryState)
def get_history_state() -> HistoryState:
    _ensure_loaded()
    return build_history_state(_history)


@router.post("/upload", response_model=list[ShiftEntry])
async def upload_history(file: UploadFile) -> list[ShiftEntry]:
    global _loaded, _source_kind, _source_label
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        entries = load_csv(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    finally:
        tmp_path.unlink(missing_ok=True)
    _history.clear()
    _history.extend(entries)
    _loaded = True
    _source_kind = "upload"
    _source_label = (file.filename or "uploaded.csv").strip() or "uploaded.csv"
    return entries


@router.get("/source", response_model=HistorySourceInfo)
def get_history_source() -> HistorySourceInfo:
    """現在メモリに載っている履歴の参照元（デフォルトパス読込 or アップロード名）。"""
    _ensure_loaded()
    if _source_label:
        return HistorySourceInfo(
            kind="upload" if _source_kind == "upload" else "default",
            label=_source_label,
            row_count=len(_history),
            default_path=_DEFAULT_REL,
        )
    if not _DEFAULT_CSV.exists() and not _history:
        hint = (
            f"{_DEFAULT_REL} が見つかりません。同じ場所に置くか、POST /history/upload でアップロードしてください。"
            if getattr(sys, "frozen", False)
            else f"{_DEFAULT_REL} が見つかりません。リポジトリに配置するか、POST /history/upload でアップロードしてください。"
        )
        return HistorySourceInfo(
            kind="empty",
            label=hint,
            row_count=0,
            default_path=_DEFAULT_REL,
        )
    return HistorySourceInfo(
        kind="empty",
        label="履歴が空です。",
        row_count=len(_history),
        default_path=_DEFAULT_REL,
    )


@router.post("/export")
def export_entries(entries: list[ShiftEntry]) -> Response:
    csv_bytes = dump_csv(normalize_entries(entries))
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=next_history.csv"},
    )


@router.get("/export")
def export_history() -> Response:
    _ensure_loaded()
    csv_bytes = dump_csv(_history)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=history.csv"},
    )
