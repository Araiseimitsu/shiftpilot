"""FastAPI エントリ。"""
from contextlib import asynccontextmanager
from pathlib import Path
import sys

# `uv run -m uvicorn app.main:app`（cwd=backend）のように起動しても
# `backend` パッケージを import できるよう、先にリポジトリルートを PYTHONPATH に入れる。
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.project_root import project_root as _project_root

_PROJECT_ROOT = _project_root()
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"

from backend.app.api import manual_staff, members, ng_entries, history, schedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリ起動時にデフォルトCSVを読み込む（初回リクエストの遅延を防ぐ）
    history.load_default_csv()
    yield


app = FastAPI(title="ShiftPilot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    members.router,
    ng_entries.router,
    history.router,
    schedule.router,
    manual_staff.router,
):
    app.include_router(router)
    app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def spa_fallback(path: str) -> FileResponse:
    if _FRONTEND_DIST.exists():
        dist_root = _FRONTEND_DIST.resolve()
        target = (_FRONTEND_DIST / path).resolve()
        if target.is_file() and (target == dist_root or dist_root in target.parents):
            return FileResponse(target)

    index = _FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return FileResponse(_PROJECT_ROOT / "frontend" / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000)
