from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# `python backend/app/main.py` や `uvicorn app.main:app` でも
# `backend.app...` の絶対 import が解決できるようにする。
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.app.api import members, ng_entries, history, schedule


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

app.include_router(members.router)
app.include_router(ng_entries.router)
app.include_router(history.router)
app.include_router(schedule.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000)
