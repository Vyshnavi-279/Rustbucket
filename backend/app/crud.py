from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
from app.models import Repo, Scan, Finding

def get_or_create_repo(db: Session, url: str, owner: str, name: str):
    repo = db.query(Repo).filter(Repo.url == url).first()
    if not repo:
        repo = Repo(url=url, owner=owner, name=name)
        db.add(repo)
        db.commit()
        db.refresh(repo)
    return repo

def create_scan(db: Session, repo_id: int):
    scan = Scan(repo_id=repo_id, status="queued")
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan

def update_scan_status(db: Session, scan_id: int, status: str, error: str = None):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.status = status
        if status == "running":
            scan.started_at = datetime.datetime.utcnow()
        elif status in ["done", "failed"]:
            scan.finished_at = datetime.datetime.utcnow()
        if error:
            scan.error = error
        db.commit()
        db.refresh(scan)
    return scan

def save_result(db: Session, scan_id: int, score: int, summary: dict, warnings: list, findings: list):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        return None
    scan.score = score
    scan.summary = summary
    scan.warnings = warnings
    scan.status = "done"
    scan.finished_at = datetime.datetime.utcnow()

    # Save individual findings
    for item in findings:
        finding = Finding(scan_id=scan_id, type=item["type"], payload=item["payload"])
        db.add(finding)

    db.commit()
    db.refresh(scan)
    return scan

def get_scan_with_result(db: Session, scan_id: int):
    return db.query(Scan).filter(Scan.id == scan_id).first()

def list_repos_with_latest(db: Session):
    repos = db.query(Repo).all()
    result = []
    for repo in repos:
        latest_scan = (
            db.query(Scan)
            .filter(Scan.repo_id == repo.id, Scan.status == "done")
            .order_by(Scan.created_at.desc())
            .first()
        )
        total_scans = db.query(Scan).filter(Scan.repo_id == repo.id).count()
        result.append({
            "repo_id": repo.id,
            "url": repo.url,
            "latest_score": latest_scan.score if latest_scan else None,
            "last_scan_at": latest_scan.finished_at.isoformat() if latest_scan and latest_scan.finished_at else None,
            "scan_count": total_scans
        })
    return result

def get_history(db: Session, repo_id: int):
    scans = (
        db.query(Scan)
        .filter(Scan.repo_id == repo_id, Scan.status == "done")
        .order_by(Scan.created_at.asc())
        .all()
    )
    return [
        {
            "scan_id": s.id,
            "date": s.finished_at.isoformat() if s.finished_at else s.created_at.isoformat(),
            "score": s.score
        }
        for s in scans
    ]