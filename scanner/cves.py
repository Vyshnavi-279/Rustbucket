"""CVE scanning via Trivy, with an OSV.dev fallback.

``scan_cves`` takes the Section 2.3 dependency list and returns a tuple
``(vulnerabilities, warnings)`` where ``vulnerabilities`` is the list
described in Section 2.4 and ``warnings`` is a list of human readable
strings collected while scanning.
"""

import json
import os
import subprocess
import tempfile

import requests

from scanner.errors import ScanError

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

TRIVY_TIMEOUT = 180
_OSV_QUERY_URL = "https://api.osv.dev/v1/query"
TRIVY_UNAVAILABLE_WARNING = "Trivy unavailable, used OSV.dev"


def _normalize_severity(severity):
    """Map any severity string to CRITICAL | HIGH | MEDIUM | LOW."""
    if not severity:
        return "LOW"
    key = str(severity).strip().upper()
    if key in SEVERITY_ORDER:
        return key
    if key in ("UNKNOWN", "NONE", "INFO"):
        return "LOW"
    if key == "MODERATE":
        return "MEDIUM"
    return "LOW"


def _parse_trivy_json(data, deps_by_name_ecosystem=None):
    """Convert a Trivy ``fs`` JSON document into the contract shape.

    Trivy reports each package under ``Results[].Vulnerabilities[]`` with
    fields ``PkgName``, ``InstalledVersion``, ``VulnerabilityID``,
    ``Severity``, ``FixedVersion`` and ``Title``.
    """
    findings = []
    seen = set()
    results = data.get("Results", []) if isinstance(data, dict) else []
    for result in results:
        for vuln in result.get("Vulnerabilities", []) or []:
            package = vuln.get("PkgName")
            if not package:
                continue
            cve_id = vuln.get("VulnerabilityID")
            if not cve_id:
                continue
            key = (package, cve_id)
            if key in seen:
                continue
            seen.add(key)
            fixed_version = vuln.get("FixedVersion")
            if fixed_version == "" or fixed_version is None:
                fixed_version = None
            findings.append(
                {
                    "package": package,
                    "version": vuln.get("InstalledVersion"),
                    "cve_id": cve_id,
                    "severity": _normalize_severity(vuln.get("Severity")),
                    "fixed_version": fixed_version,
                    "title": vuln.get("Title"),
                }
            )
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["package"]))
    return findings


def _cvss_score_to_severity(score):
    try:
        score = float(score)
    except (TypeError, ValueError):
        return None
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


def _is_numeric(value):
    if isinstance(value, (int, float)):
        return True
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _osv_severity(vuln):
    """Borrow the reporter's severity first, then a numeric CVSS score."""
    db_severity = (vuln.get("database_specific") or {}).get("severity")
    if db_severity and str(db_severity).upper() in SEVERITY_ORDER:
        return str(db_severity).upper()
    for entry in vuln.get("severity", []) or []:
        score = entry.get("score")
        if _is_numeric(score):
            graded = _cvss_score_to_severity(score)
            if graded:
                return graded
    return "LOW"


def _parse_osv_vulns(data, dep):
    """Map an OSV.dev query response for a single dependency to contract items."""
    findings = []
    for vuln in (data or {}).get("vulns", []) or []:
        if not vuln:
            continue
        severity = _osv_severity(vuln)
        fixed_version = None
        for affected in vuln.get("affected", []) or []:
            for rng in affected.get("ranges", []) or []:
                for event in rng.get("events", []) or []:
                    if "fixed" in event:
                        fixed_version = event["fixed"]
                        break
                if fixed_version:
                    break
            if fixed_version:
                break
        findings.append(
            {
                "package": dep["name"],
                "version": dep.get("version"),
                "cve_id": vuln.get("id"),
                "severity": severity,
                "fixed_version": fixed_version,
                "title": vuln.get("summary"),
            }
        )
    return findings


def _scan_osv(deps):
    """Query the free OSV.dev API for each dependency."""
    findings = []
    for dep in deps:
        payload = {
            "package": {
                "name": dep["name"],
                "ecosystem": "PyPI" if dep["ecosystem"] == "pypi" else "npm",
            },
            "version": dep["version"],
        }
        try:
            resp = requests.post(_OSV_QUERY_URL, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.RequestException:
            continue
        findings.extend(_parse_osv_vulns(resp.json(), dep))
    seen = set()
    deduped = []
    for finding in findings:
        key = (finding["package"], finding["cve_id"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    deduped.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["package"]))
    return deduped


def _write_trivy_manifests(tmpdir, deps):
    """Write dependency manifests into ``tmpdir`` that Trivy can scan."""
    requirements_lines = []
    lockfile_packages = {
        "": {"name": "scan", "version": "1.0.0"},
    }
    has_pypi = False
    has_npm = False
    for dep in deps:
        if dep["ecosystem"] == "pypi":
            has_pypi = True
            requirements_lines.append(f"{dep['name']}=={dep['version']}")
        else:
            has_npm = True
            node_path = f"node_modules/{dep['name']}"
            lockfile_packages[node_path] = {"version": dep["version"]}
    if has_pypi:
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as fh:
            fh.write("\n".join(requirements_lines) + "\n")
    if has_npm:
        lockfile = {
            "name": "scan",
            "lockfileVersion": 3,
            "requires": True,
            "packages": lockfile_packages,
        }
        with open(os.path.join(tmpdir, "package-lock.json"), "w") as fh:
            json.dump(lockfile, fh)


def _run_trivy(tmpdir):
    """Run Trivy against ``tmpdir`` and return the parsed JSON document."""
    command = [
        "trivy",
        "fs",
        "--scanners",
        "vuln",
        "--format",
        "json",
        "--quiet",
        tmpdir,
    ]
    env = os.environ.copy()
    cache_dir = os.environ.get("TRIVY_CACHE_DIR")
    if cache_dir:
        env["TRIVY_CACHE_DIR"] = cache_dir
        env["XDG_CACHE_HOME"] = cache_dir
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TRIVY_TIMEOUT,
            env=env,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        raise ScanError(f"CVE scan failed: {_short_message(exc)}") from exc
    if result.returncode != 0:
        raise ScanError("CVE scan failed: Trivy exited with an error")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ScanError("CVE scan failed: could not parse Trivy output") from exc


def _short_message(exc):
    message = f"{type(exc).__name__}: {exc}"
    return message[:300]


def scan_cves(deps):
    """Scan dependencies for known vulnerabilities.

    Returns ``(vulnerabilities, warnings)``. Uses the Trivy binary when
    available and automatically falls back to the OSV.dev API otherwise.
    """
    warnings = []
    skipped = []
    for dep in deps:
        version = dep.get("version")
        if not version or version == "unknown":
            skipped.append(dep["name"])
    if skipped:
        warnings.append(f"Skipped CVE scan for {len(skipped)} package(s) with unknown version")
    scan_deps = [d for d in deps if d.get("version") and d.get("version") != "unknown"]
    if not scan_deps:
        return [], warnings
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_trivy_manifests(tmpdir, scan_deps)
            data = _run_trivy(tmpdir)
        return _parse_trivy_json(data), warnings
    except ScanError:
        try:
            return _scan_osv(scan_deps), warnings + [TRIVY_UNAVAILABLE_WARNING]
        except requests.RequestException as exc:
            raise ScanError("CVE scan failed") from exc