import requests
import requests_mock

from scanner import registry


def test_fetch_npm_plain_package():
    with requests_mock.Mocker() as m:
        m.get(
            "https://registry.npmjs.org/lodash/latest",
            json={"version": "4.17.21", "license": "MIT"},
        )
        info = registry.fetch_registry_info({"name": "lodash", "version": "4.17.15", "ecosystem": "npm"})
    assert info == {"latest": "4.17.21", "license": "MIT", "license_classifiers": []}


def test_fetch_npm_scoped_package_encoded():
    with requests_mock.Mocker() as m:
        m.get(
            "https://registry.npmjs.org/@babel%2Fcore/latest",
            json={"version": "7.20.0", "license": {"type": "MIT"}},
        )
        info = registry.fetch_registry_info(
            {"name": "@babel/core", "version": "7.19.0", "ecosystem": "npm"}
        )
    assert info["latest"] == "7.20.0"
    assert info["license"] == "MIT"


def test_fetch_pypi_with_classifiers():
    with requests_mock.Mocker() as m:
        m.get(
            "https://pypi.org/pypi/django/json",
            json={
                "info": {
                    "version": "4.2.5",
                    "license": "",
                    "classifiers": [
                        "Programming Language :: Python :: 3",
                        "License :: OSI Approved :: BSD License",
                    ],
                }
            },
        )
        info = registry.fetch_registry_info({"name": "django", "version": "2.2.0", "ecosystem": "pypi"})
    assert info["latest"] == "4.2.5"
    assert info["license"] is None
    assert info["license_classifiers"] == ["License :: OSI Approved :: BSD License"]


def test_fetch_pypi_uses_license_expression():
    with requests_mock.Mocker() as m:
        m.get(
            "https://pypi.org/pypi/pylint/json",
            json={
                "info": {
                    "version": "3.2.0",
                    "license": None,
                    "license_expression": "GPL-2.0-or-later",
                    "classifiers": [],
                }
            },
        )
        info = registry.fetch_registry_info({"name": "pylint", "version": "2.5.3", "ecosystem": "pypi"})
    assert info["license"] == "GPL-2.0-or-later"


def test_fetch_registry_returns_none_on_failure():
    with requests_mock.Mocker() as m:
        m.get(
            "https://registry.npmjs.org/nope-nonexistent/latest",
            exc=requests.ConnectTimeout,
        )
        info = registry.fetch_registry_info(
            {"name": "nope-nonexistent", "version": "1.0.0", "ecosystem": "npm"}
        )
    assert info is None


def test_fetch_registry_retries_then_returns_none():
    hits = {"count": 0}

    def handler(request, context):
        hits["count"] += 1
        raise requests.HTTPError("500")

    with requests_mock.Mocker() as m:
        m.get("https://registry.npmjs.org/boom/latest", exc=requests.HTTPError)
        info = registry.fetch_registry_info({"name": "boom", "version": "1.0.0", "ecosystem": "npm"})
    assert info is None


def test_fetch_all_registry_info_concurrent_and_counts_failures():
    with requests_mock.Mocker() as m:
        m.get("https://registry.npmjs.org/lodash/latest", json={"version": "4.17.21", "license": "MIT"})
        m.get("https://pypi.org/pypi/flask/json", json={"info": {"version": "2.3.0", "license": "BSD-3-Clause"}})
        m.get("https://registry.npmjs.org/boom/latest", exc=requests.ConnectionError)
        deps = [
            {"name": "lodash", "version": "4.17.15", "ecosystem": "npm"},
            {"name": "flask", "version": "1.1.2", "ecosystem": "pypi"},
            {"name": "boom", "version": "1.0.0", "ecosystem": "npm"},
        ]
        info, failures = registry.fetch_all_registry_info(deps)
    assert failures == 1
    assert ("npm", "lodash") in info
    assert ("pypi", "flask") in info


def test_fetch_all_registry_info_deduplicates():
    with requests_mock.Mocker() as m:
        m.get("https://registry.npmjs.org/lodash/latest", json={"version": "4.17.21", "license": "MIT"})
        deps = [
            {"name": "lodash", "version": "4.17.15", "ecosystem": "npm"},
            {"name": "lodash", "version": "4.17.15", "ecosystem": "npm"},
        ]
        info, _failures = registry.fetch_all_registry_info(deps)
    assert len(info) == 1


def test_clear_cache(monkeypatch):
    registry._cache[("npm", "lodash")] = "cached"
    registry.clear_cache()
    assert registry._cache == {}