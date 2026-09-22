import json
import os
from types import SimpleNamespace

import pytest

from scanner.cves import (
    _parse_osv_vulns,
    _parse_trivy_json,
    _scan_osv,
    scan_cves,
)
from scanner.errors import ScanError

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "trivy_output.json")


def _load_fixture():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def test_parse_trivy_json_maps_contract_shape():
    findings = _parse_trivy_json(_load_fixture())
    assert len(findings) == 5
    first = findings[0]
    assert set(first) == {
        "package",
        "version",
        "cve_id",
        "severity",
        "fixed_version",
        "title",
    }
    assert first["package"] == "lodash"
    assert first["severity"] == "CRITICAL"
    assert first["fixed_version"] == "4.17.21"


def test_parse_trivy_json_sorted_by_severity_then_package():
    findings = _parse_trivy_json(_load_fixture())
    severities = [f["severity"] for f in findings]
    assert severities == ["CRITICAL", "HIGH", "MEDIUM", "MEDIUM", "LOW"]


def test_parse_trivy_json_maps_unknown_to_low():
    findings = _parse_trivy_json(_load_fixture())
    unknown = next(f for f in findings if f["cve_id"] == "CVE-2021-31542")
    assert unknown["severity"] == "LOW"
    assert unknown["fixed_version"] is None


def test_parse_trivy_json_deduplicates_on_package_cve():
    data = _load_fixture()
    duplicate = data["Results"][0]["Vulnerabilities"][0]
    data["Results"][0]["Vulnerabilities"].append(duplicate)
    assert len(_parse_trivy_json(data)) == 5


def test_parse_trivy_json_handles_empty_results():
    assert _parse_trivy_json({}) == []
    assert _parse_trivy_json({"Results": []}) == []
    assert _parse_trivy_json({"Results": [{}]}) == []


def test_scan_cves_uses_trivy_and_parses_output(monkeypatch):
    captured = []

    def fake_run(command, **kwargs):
        captured.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps(_load_fixture()))

    monkeypatch.setattr("scanner.cves.subprocess.run", fake_run)
    vulns, warnings = scan_cves(
        [
            {"name": "django", "version": "2.2.0", "ecosystem": "pypi"},
            {"name": "lodash", "version": "4.17.15", "ecosystem": "npm"},
        ]
    )
    assert len(vulns) == 5
    assert any(v["cve_id"] == "CVE-2021-23337" for v in vulns)
    assert warnings == []
    assert captured[0][0] == "trivy"
    assert "--scanners" in captured[0]


def test_scan_cves_skips_unknown_version_with_warning():
    warnings = []
    vulns = []
    deps = [
        {"name": "lodash", "version": "unknown", "ecosystem": "npm"},
        {"name": "flask", "version": "unknown", "ecosystem": "pypi"},
    ]
    vulns, warnings = scan_cves(deps)
    assert vulns == []
    assert any("unknown version" in w for w in warnings)


def test_scan_cves_empty_deps():
    assert scan_cves([]) == ([], [])


def test_scan_cves_falls_back_to_osv_when_trivy_missing(monkeypatch):
    def missing_binary(*args, **kwargs):
        raise FileNotFoundError("no trivy")

    monkeypatch.setattr("scanner.cves.subprocess.run", missing_binary)
    monkeypatch.setattr(
        "scanner.cves._scan_osv",
        lambda deps: [{"package": "lodash", "version": "4.17.15",
                        "cve_id": "CVE-2021-23337", "severity": "HIGH",
                        "fixed_version": "4.17.21", "title": "x"}],
    )
    vulns, warnings = scan_cves([{"name": "lodash", "version": "4.17.15", "ecosystem": "npm"}])
    assert len(vulns) == 1
    assert "Trivy unavailable, used OSV.dev" in warnings


def test_scan_cves_falls_back_to_osv_when_trivy_fails(monkeypatch):
    def failing_binary(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr("scanner.cves.subprocess.run", failing_binary)
    monkeypatch.setattr(
        "scanner.cves._scan_osv",
        lambda deps: [{"package": "lodash", "version": "4.17.15",
                        "cve_id": "CVE-2021-23337", "severity": "LOW",
                        "fixed_version": None, "title": "x"}],
    )
    vulns, warnings = scan_cves([{"name": "lodash", "version": "4.17.15", "ecosystem": "npm"}])
    assert len(vulns) == 1
    assert "Trivy unavailable, used OSV.dev" in warnings


def test_scan_cves_raises_scan_error_when_both_fail(monkeypatch):
    import requests

    def missing_binary(*args, **kwargs):
        raise FileNotFoundError("no trivy")

    def osv_down(deps):
        raise requests.RequestException("network down")

    monkeypatch.setattr("scanner.cves.subprocess.run", missing_binary)
    monkeypatch.setattr("scanner.cves._scan_osv", osv_down)
    with pytest.raises(ScanError):
        scan_cves([{"name": "lodash", "version": "4.17.15", "ecosystem": "npm"}])


def test_parse_osv_vulns_maps_osv_response():
    data = {
        "vulns": [
            {
                "id": "CVE-2021-23337",
                "summary": "Command injection",
                "severity": [{"type": "CVSS_V3", "score": "9.8"}],
                "affected": [
                    {
                        "package": {"name": "lodash", "ecosystem": "npm"},
                        "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "4.17.21"}]}],
                    }
                ],
            },
            {
                "id": "GHSA-1234",
                "summary": None,
                "database_specific": {"severity": "MEDIUM"},
                "affected": [{"package": {"name": "lodash"}, "ranges": []}],
            },
        ]
    }
    dep = {"name": "lodash", "version": "4.17.15", "ecosystem": "npm"}
    findings = _parse_osv_vulns(data, dep)
    assert len(findings) == 2
    assert findings[0]["cve_id"] == "CVE-2021-23337"
    assert findings[0]["severity"] == "CRITICAL"
    assert findings[0]["fixed_version"] == "4.17.21"


@pytest.mark.network
def test_scan_osv_hits_real_api():
    findings = _scan_osv([{"name": "lodash", "version": "4.17.15", "ecosystem": "npm"}])
    assert any(f["cve_id"] == "CVE-2021-23337" for f in findings)