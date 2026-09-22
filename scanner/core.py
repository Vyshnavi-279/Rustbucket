"""The public scan orchestration: ``run_scan``.

This module is the only thing Person 1's worker needs: give it the
Section 2.3 dependency list and it returns the Section 2.4 result.
"""

from concurrent.futures import ThreadPoolExecutor

from scanner.cves import scan_cves
from scanner.licenses import check_licenses
from scanner.outdated import check_outdated
from scanner.registry import fetch_all_registry_info
from scanner.score import build_summary, compute_score

VALID_ECOSYSTEMS = {"npm", "pypi"}


def _validate_deps(deps):
    """Drop invalid items and duplicate ``(name, ecosystem)`` pairs."""
    clean = []
    warnings = []
    seen = set()
    for dep in deps or []:
        if not isinstance(dep, dict):
            warnings.append("Dropped an invalid dependency entry")
            continue
        name = dep.get("name")
        version = dep.get("version")
        ecosystem = dep.get("ecosystem")
        if not name or not isinstance(name, str):
            warnings.append("Dropped a dependency with no name")
            continue
        if ecosystem not in VALID_ECOSYSTEMS:
            warnings.append(f"Dropped dependency {name!r} with unknown ecosystem")
            continue
        if version is None:
            version = "unknown"
        key = (ecosystem, name)
        if key in seen:
            warnings.append(f"Dropped duplicate dependency {name}")
            continue
        seen.add(key)
        clean.append({"name": name, "version": version, "ecosystem": ecosystem})
    return clean, warnings


def _major_outdated_count(outdated):
    return sum(1 for item in outdated if item.get("update_type") == "major")


def run_scan(deps, project_license=None):
    """Scan a dependency list and return the Section 2.4 result.

    ``deps`` is a list of ``{name, version, ecosystem}`` objects
    (Section 2.3); ``project_license`` may be ``None`` or an SPDX id.
    Raises :class:`scanner.errors.ScanError` if the CVE scan itself
    fails completely.
    """
    cleaned_deps, warnings = _validate_deps(deps)

    if not cleaned_deps:
        return {
            "score": 100,
            "summary": {
                "total_dependencies": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "outdated": 0,
                "license_issues": 0,
            },
            "vulnerabilities": [],
            "outdated": [],
            "license_issues": [],
            "warnings": warnings,
        }

    with ThreadPoolExecutor(max_workers=2) as pool:
        cve_future = pool.submit(scan_cves, cleaned_deps)
        registry_future = pool.submit(fetch_all_registry_info, cleaned_deps)
        vulnerabilities, cve_warnings = cve_future.result()
        registry_info, failures = registry_future.result()

    warnings.extend(cve_warnings)
    if failures:
        warnings.append(f"Registry lookup failed for {failures} packages")

    outdated, _skipped = check_outdated(cleaned_deps, registry_info)
    license_issues = check_licenses(cleaned_deps, registry_info, project_license)

    summary = build_summary(cleaned_deps, vulnerabilities, outdated, license_issues)
    score = compute_score(summary, _major_outdated_count(outdated))

    return {
        "score": score,
        "summary": summary,
        "vulnerabilities": vulnerabilities,
        "outdated": outdated,
        "license_issues": license_issues,
        "warnings": warnings,
    }