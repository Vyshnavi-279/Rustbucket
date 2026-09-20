"""Package registry lookups for npm and PyPI.

One request per package feeds both the outdated check and the license
check. Results are cached for the duration of a run, lookups run
concurrently, and a failed lookup returns ``None`` instead of raising.
"""

from concurrent.futures import ThreadPoolExecutor

import requests

NPM_URL = "https://registry.npmjs.org/{name}/latest"
PYPI_URL = "https://pypi.org/pypi/{name}/json"

TIMEOUT = 10
MAX_WORKERS = 10

_cache = {}


def _dep_key(dep):
    return (dep["ecosystem"], dep["name"])


def fetch_registry_info(dep):
    """Return ``{latest, license, license_classifiers}`` or ``None`` on failure."""
    key = _dep_key(dep)
    if key in _cache:
        return _cache[key]
    info = None
    if dep["ecosystem"] == "npm":
        info = _fetch_npm(dep["name"])
    elif dep["ecosystem"] == "pypi":
        info = _fetch_pypi(dep["name"])
    _cache[key] = info
    return info


def _get(url):
    last_error = None
    for _ in range(2):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
    raise last_error


def _fetch_npm(name):
    encoded = name.replace("/", "%2F")
    try:
        data = _get(NPM_URL.format(name=encoded))
    except requests.RequestException:
        return None
    license_value = data.get("license")
    if isinstance(license_value, dict):
        license_value = license_value.get("type")
    elif isinstance(license_value, list):
        license_value = license_value[0] if license_value else None
    return {
        "latest": data.get("version"),
        "license": license_value,
        "license_classifiers": [],
    }


def _fetch_pypi(name):
    try:
        data = _get(PYPI_URL.format(name=name))
    except requests.RequestException:
        return None
    info = data.get("info", {})
    classifiers = [
        line
        for line in info.get("classifiers", []) or []
        if str(line).startswith("License ::")
    ]
    license_value = info.get("license") or info.get("license_expression")
    return {
        "latest": info.get("version"),
        "license": license_value,
        "license_classifiers": classifiers,
    }


def fetch_all_registry_info(deps):
    """Fetch registry info for every dependency concurrently.

    Returns a tuple ``(info_by_key, failures)`` where ``info_by_key`` is
    a dict keyed by ``(ecosystem, name)`` (omitting any package whose
    lookup failed) and ``failures`` is the number of failed lookups.
    """
    unique = {}
    for dep in deps:
        if dep.get("name"):
            unique[(dep["ecosystem"], dep["name"])] = dep
    results = {}
    failures = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_to_key = {
            pool.submit(fetch_registry_info, dep): key
            for key, dep in unique.items()
        }
        for future, key in future_to_key.items():
            info = future.result()
            if info is not None:
                results[key] = info
            else:
                failures += 1
    return results, failures


def clear_cache():
    """Reset the per-run cache (used by tests)."""
    _cache.clear()