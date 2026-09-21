import time

from app import crud, github_client, manifest_parser, scanner_adapter
from app.config import settings
from app.db import SessionLocal
from celery import Celery
from prometheus_client import Counter, Histogram, start_http_server

celery_app = Celery("rustbucket_worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_time_limit = 300

# Prometheus Worker Metrics
SCANS_STARTED = Counter("rustbucket_scans_started_total", "Total scans started")
SCANS_COMPLETED = Counter("rustbucket_scans_completed_total", "Total scans completed successfully")
SCANS_FAILED = Counter("rustbucket_scans_failed_total", "Total scans failed")
SCAN_DURATION = Histogram("rustbucket_scan_duration_seconds", "Histogram of scan duration")

# Start Prometheus metrics exporter on port 8001
try:
    start_http_server(8001)
except Exception:  # noqa: BLE001, S110 -- metrics server is best-effort, must not crash the worker
    pass

@celery_app.task(name="app.worker.run_scan_task")
def run_scan_task(scan_id: int):
    SCANS_STARTED.inc()
    start_time = time.time()
    db = SessionLocal()
    
    try:
        crud.update_scan_status(db, scan_id, "running")
        scan = crud.get_scan_with_result(db, scan_id)
        repo_data = github_client.fetch_repo_data(scan.repo.url)
        
        # Save repo license
        scan.repo.license = repo_data["license"]
        db.commit()

        deps = manifest_parser.parse_manifests(repo_data["files"])
        if not deps:
            raise github_client.NoManifestFound("No parseable dependencies found in manifests.")

        result = scanner_adapter.run_scan(deps, repo_data["license"])

        # Construct findings list
        findings = []
        for v in result["summary"].get("vulnerabilities", []):
            findings.append({"type": "vulnerability", "payload": v})
        for o in result["summary"].get("outdated", []):
            findings.append({"type": "outdated", "payload": o})
        for l in result["summary"].get("license_issues", []):
            findings.append({"type": "license_issue", "payload": l})

        crud.save_result(
            db=db,
            scan_id=scan_id,
            score=result["score"],
            summary=result["summary"],
            warnings=result["summary"].get("warnings", []),
            findings=findings
        )
        
        SCANS_COMPLETED.inc()
        SCAN_DURATION.observe(time.time() - start_time)
    except Exception as e:  # noqa: BLE001 -- task must never leave a scan stuck in "running" (see plan 1.6)
        SCANS_FAILED.inc()
        crud.update_scan_status(db, scan_id, "failed", error=str(e))
    finally:
        db.close()
