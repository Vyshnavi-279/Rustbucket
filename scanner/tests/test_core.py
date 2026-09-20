import json

import pytest

from scanner.core import _validate_deps, run_scan
from scanner.errors import ScanError


def test_validate_drops_invalid_and_duplicates():
    deps = [
        {"name": "a", "version": "1.0.0", "ecosystem": "npm"},
        {"name": "a", "version": "1.0.0", "ecosystem": "npm"},
        {"name": "b", "version": "1.0.0", "ecosystem": "maven"},
        {"name": "c", "version": "1.0.0", "ecosystem": "pypi"},
        "not-a-dict",
        {},
        {"name": "", "version": "1.0.0", "ecosystem": "npm"},
    ]
    clean, warnings = _validate_deps(deps)
    assert [d["name"] for d in clean] == ["a", "c"]
    assert len(warnings) == 5


def test_validate_normalizes_none_version():
    clean, _ = _validate_deps([{"name": "x", "version": None, "ecosystem": "npm"}])
    assert clean[0]["version"] == "unknown"


def test_empty_deps_result():
    result = run_scan([])
    assert result["score"] == 100
    assert result["summary"]["total_dependencies"] == 0
    assert result["vulnerabilities"] == []
    assert result["outdated"] == []
    assert result["license_issues"] == []
    assert isinstance(result["warnings"], list)


def test_run_scan_full_flow(monkeypatch):
    vulns = [
        {"package": "lodash", "version": "4.17.15", "cve_id": "CVE-2021-23337",
         "severity": "CRITICAL", "fixed_version": "4.17.21", "title": "cmd injection"},
    ]
    registry_info = {
        ("npm", "lodash"): {"latest": "4.17.21", "license": "MIT", "license_classifiers": []},
        ("pypi", "pylint"): {"latest": "3.2.0", "license": "GPL-2.0-or-later", "license_classifiers": []},
    }
    monkeypatch.setattr("scanner.core.scan_cves", lambda deps: (vulns, []))
    monkeypatch.setattr("scanner.core.fetch_all_registry_info", lambda deps: (registry_info, 0))

    deps = [
        {"name": "lodash", "version": "4.17.15", "ecosystem": "npm"},
        {"name": "pylint", "version": "2.5.0", "ecosystem": "pypi"},
    ]
    result = run_scan(deps, "MIT")

    assert set(result) == {"score", "summary", "vulnerabilities", "outdated", "license_issues", "warnings"}
    assert result["score"] == 73  # 100 -15(critical) -2(major outdated) -10(license conflict)
    assert result["summary"]["total_dependencies"] == 2
    assert result["vulnerabilities"][0]["cve_id"] == "CVE-2021-23337"


def test_run_scan_returns_json_serializable(monkeypatch):
    monkeypatch.setattr("scanner.core.scan_cves", lambda deps: ([], []))
    monkeypatch.setattr(
        "scanner.core.fetch_all_registry_info",
        lambda deps: ({
            ("npm", "lodash"): {"latest": "4.17.21", "license": "MIT", "license_classifiers": []},
        }, 0),
    )
    result = run_scan([{"name": "lodash", "version": "4.17.15", "ecosystem": "npm"}], "MIT")
    json.dumps(result)


def test_registry_failure_adds_warning(monkeypatch):
    monkeypatch.setattr("scanner.core.scan_cves", lambda deps: ([], []))
    monkeypatch.setattr("scanner.core.fetch_all_registry_info", lambda deps: ({}, 2))
    result = run_scan([{"name": "a", "version": "1.0.0", "ecosystem": "npm"}])
    assert any("Registry lookup failed for 2 packages" in w for w in result["warnings"])


def test_scan_error_propagates(monkeypatch):
    def boom(deps):
        raise ScanError("CVE scan failed")

    monkeypatch.setattr("scanner.core.scan_cves", boom)
    with pytest.raises(ScanError):
        run_scan([{"name": "a", "version": "1.0.0", "ecosystem": "npm"}], None)