
from pydantic import BaseModel


class ScanCreateRequest(BaseModel):
    repo_url: str

class ScanCreateResponse(BaseModel):
    scan_id: int
    repo_id: int
    status: str

class RepoResponse(BaseModel):
    repo_id: int
    url: str
    latest_score: int | None = None
    last_scan_at: str | None = None
    scan_count: int

class HistoryItemResponse(BaseModel):
    scan_id: int
    date: str
    score: int | None = None