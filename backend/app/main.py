import redis
from app import crud, github_client
from app.config import settings
from app.db import get_db
from app.schemas import (
    HistoryItemResponse,
    RepoResponse,
    ScanCreateRequest,
    ScanCreateResponse,
)
from app.worker import run_scan_task
from fastapi import Depends, FastAPI, HTTPException
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

app = FastAPI(title="Rustbucket Backend API", version="1.0.0")

# Instrument Prometheus metrics on /metrics
Instrumentator().instrument(app).expose(app)

# Queue length metric gauge
redis_client = redis.Redis.from_url(settings.REDIS_URL)
queue_gauge = Gauge("rustbucket_queue_length", "Number of jobs waiting in Redis queue")

@app.middleware("http")
async def update_queue_gauge(request, call_next):
    try:
        length = redis_client.llen("celery")
        queue_gauge.set(length)
    except Exception:  # noqa: BLE001, S110 -- best-effort metric, must not break the request
        pass
    return await call_next(request)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/scans", status_code=202, response_model=ScanCreateResponse)
def submit_scan(req: ScanCreateRequest, db: Session = Depends(get_db)):
    try:
        owner, name = github_client.parse_repo_url(req.repo_url)
    except github_client.InvalidRepoURL as e:
        raise HTTPException(status_code=400, detail=str(e))

    normalized_url = f"https://github.com/{owner.lower()}/{name.lower()}"
    repo = crud.get_or_create_repo(db, url=normalized_url, owner=owner, name=name)
    
    scan = crud.create_scan(db, repo.id)
    run_scan_task.delay(scan.id)
    
    return {"scan_id": scan.id, "repo_id": repo.id, "status": "queued"}

@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = crud.get_scan_with_result(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    result_data = None
    if scan.status == "done":
        result_data = {
            "score": scan.score,
            "summary": scan.summary,
            "warnings": scan.warnings or []
        }

    return {
        "scan_id": scan.id,
        "repo_id": scan.repo_id,
        "repo_url": scan.repo.url,
        "status": scan.status,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
        "error": scan.error,
        "result": result_data
    }

@app.get("/api/repos", response_model=list[RepoResponse])
def get_repos(db: Session = Depends(get_db)):
    return crud.list_repos_with_latest(db)

@app.get("/api/repos/{repo_id}/history", response_model=list[HistoryItemResponse])
def get_repo_history(repo_id: int, db: Session = Depends(get_db)):
    history = crud.get_history(db, repo_id)
    if not history and not db.query(crud.Repo).filter(crud.Repo.id == repo_id).first():
        raise HTTPException(status_code=404, detail="Repo not found")
    return history

