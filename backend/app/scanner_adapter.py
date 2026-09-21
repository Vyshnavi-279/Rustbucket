import time

from app.config import settings


class ScanError(Exception): pass

def run_scan(deps: list[dict], project_license: str | None = None) -> dict:
    # Check for test failure trigger
    for dep in deps:
        if dep.get("name") == "crash-test":
            raise ScanError("Simulated scanner crash trigger.")

    if settings.SCANNER_MODE == "real":
        from scanner import run_scan as real_run_scan
        return real_run_scan(deps, project_license)

    # Stub mode simulation
    time.sleep(3)
    return {
        "score": 61,
        "summary": {
            "total_dependencies": len(deps),
            "critical": 1,
            "high": 1,
            "medium": 2,
            "low": 0,
            "vulnerabilities": [
                {
                    "package": "lodash",
                    "version": "4.17.15",
                    "cve_id": "CVE-2021-23337",
                    "severity": "HIGH",
                    "fixed_version": "4.17.21",
                    "title": "Command injection in lodash"
                }
            ],
            "outdated": [
                {"package": "express", "current": "4.16.0", "latest": "4.19.2", "update_type": "minor"}
            ],
            "license_issues": [
                {
                    "package": "pylint",
                    "license": "GPL-2.0-or-later",
                    "category": "strong_copyleft",
                    "reason": "Strong copyleft license in project"
                }
            ],
            "warnings": []
        }
    }
