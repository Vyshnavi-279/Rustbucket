import pytest

from scanner.core import run_scan
from scanner.errors import ScanError


@pytest.fixture
def fast_scanner(monkeypatch):
    """Make the slow/network parts return instantly."""
    monkeypatch.setattr("scanner.core.scan_cves", lambda deps: ([], []))
    monkeypatch.setattr("scanner.core.fetch_all_registry_info", lambda deps: ({}, 0))


def test_unicode_package_names(fast_scanner):
    deps = [{"name": "héllo-wörld-99", "version": "1.0.0", "ecosystem": "npm"}]
    result = run_scan(deps)
    assert result["summary"]["total_dependencies"] == 1


def test_huge_version_string(fast_scanner):
    deps = [{"name": "pkg", "version": "1.0.0" + "x" * 500, "ecosystem": "npm"}]
    result = run_scan(deps)
    assert result["summary"]["total_dependencies"] == 1


def test_none_values_dropped(fast_scanner):
    deps = [
        {"name": None, "version": None, "ecosystem": None},
        {"name": "fine", "version": None, "ecosystem": "pypi"},
    ]
    result = run_scan(deps)
    assert result["summary"]["total_dependencies"] == 1
    assert result["summary"]["license_issues"] == 1
    assert 0 <= result["score"] <= 100
    assert len(result["warnings"]) == 1


def test_500_dependencies_finishes(fast_scanner):
    deps = [
        {"name": f"pkg-{i}", "version": "1.0.0", "ecosystem": "npm" if i % 2 else "pypi"}
        for i in range(500)
    ]
    result = run_scan(deps)
    assert result["summary"]["total_dependencies"] == 500
    assert 0 <= result["score"] <= 100


def test_scan_error_is_exported_from_package():
    from scanner import ScanError as Exported

    assert Exported is ScanError
    assert str(ScanError("boom")) == "boom"


def test_run_scan_importable_from_package(monkeypatch):
    from scanner import run_scan as exported_run_scan

    monkeypatch.setattr("scanner.core.scan_cves", lambda deps: ([], []))
    monkeypatch.setattr("scanner.core.fetch_all_registry_info", lambda deps: ({}, 0))
    result = exported_run_scan([], "MIT")
    assert result["score"] == 100