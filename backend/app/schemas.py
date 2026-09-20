from pydantic import BaseModel
from typing import Optional, List, Any

class ScanCreateRequest(BaseModel):
    repo_url: str

class ScanCreateResponse(BaseModel):
    scan_id: int
    repo_id: int
    status: str

class RepoResponse(BaseModel):
    repo_id: int
    url: str
    latest_score: Optional[int] = None
    last_scan_at: Optional[str] = None
    scan_count: int

class HistoryItemResponse(BaseModel):
    scan_id: int
    date: str
    score: Optional[int] = None