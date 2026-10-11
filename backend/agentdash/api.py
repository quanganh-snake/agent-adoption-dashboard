from contextlib import asynccontextmanager
from pathlib import Path
import os, subprocess, sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


def _data():
    from .config import DATA_DIR
    return Path(DATA_DIR)


def _locked(source):
    from .db import lock_path
    return lock_path(source).exists()


@asynccontextmanager
async def lifespan(app):
    scheduler = None
    if os.getenv("AGENTDASH_SCHEDULER", "1") != "0":
        from .scheduler import start
        scheduler = start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/snapshots/{name}")
def snapshot(name: str):
    if name not in {"meta.json", "baseline.json", "series.json", "yearly.json", "monthly_2026.json", "paper_vs_latest.json"}:
        raise HTTPException(404)
    file = _data() / "snapshots" / name
    if not file.is_file():
        raise HTTPException(404, "Chưa có snapshot, hãy chạy agentdash export")
    return FileResponse(file, media_type="application/json")


@app.get("/api/sync/status")
def status():
    try:
        from .db import connect
        with connect("jobs") as database:
            jobs = [dict(row) for row in database.execute("SELECT * FROM job ORDER BY id DESC LIMIT 50")]
    except Exception:
        jobs = []
    return {"jobs": jobs, "locks": {source: _locked(source) for source in ("p2", "p3", "global")}}


@app.post("/api/sync/{source}", status_code=202)
def sync(source: str):
    if source not in {"p2", "p3", "global"}:
        raise HTTPException(404)
    from .db import acquire_lock, release_lock
    if not acquire_lock(source):
        raise HTTPException(409, "Đang có job chạy")
    try:
        args = [sys.executable, "-m", "agentdash.cli", "sync", source, "--lock-held"]
        if source == "p3":
            args += ["--enrich", "--max-minutes", "50"]
        subprocess.Popen(args)
    except Exception:
        release_lock(source)
        raise
    return {"source": source, "status": "started"}
