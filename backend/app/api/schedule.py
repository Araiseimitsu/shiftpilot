from fastapi import APIRouter, HTTPException
from backend.app.core.solver import generate_schedule
from backend.app.schemas.schedule import ScheduleRequest, ScheduleResult
from backend.app.api import ng_entries as ng_store
from backend.app.api import history as history_store


router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/generate", response_model=ScheduleResult)
def generate(request: ScheduleRequest) -> ScheduleResult:
    # NG情報と履歴をリクエストに注入（フロントが省略した場合はサーバー側のストアを使用）
    if not request.ng_entries:
        request = request.model_copy(update={"ng_entries": list(ng_store._store)})
    if not request.history:
        history_store._ensure_loaded()
        request = request.model_copy(update={"history": list(history_store._history)})
    try:
        return generate_schedule(request)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
