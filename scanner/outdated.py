"""Outdated package detection against live registry versions."""

from packaging.version import InvalidVersion, Version


def _primary_components(version):
    return [part for part in version.release if isinstance(part, int)]


def _update_type(current, latest):
    """major if the first number differs, minor if the second differs, else patch."""
    cur = _primary_components(current)
    lat = _primary_components(latest)
    if not cur or not lat:
        return "major"
    if lat[0] > cur[0]:
        return "major"
    if len(cur) < 2 or len(lat) < 2:
        return "minor" if lat[0] > cur[0] else "patch"
    if lat[1] > cur[1]:
        return "minor"
    return "patch"


def check_outdated(deps, registry_info):
    """Compare installed vs latest versions.

    ``registry_info`` maps ``(ecosystem, name)`` to
    ``{latest, license, license_classifiers}`` as returned by
    :func:`scanner.registry.fetch_all_registry_info`.
    """
    outdated = []
    skipped = 0
    for dep in deps:
        version = dep.get("version")
        if not version or version == "unknown":
            skipped += 1
            continue
        info = registry_info.get((dep["ecosystem"], dep["name"]))
        if info is None or not info.get("latest"):
            skipped += 1
            continue
        current = info["latest"]
        try:
            current_v = Version(version)
            latest_v = Version(current)
        except InvalidVersion:
            skipped += 1
            continue
        if latest_v <= current_v:
            continue
        outdated.append(
            {
                "package": dep["name"],
                "current": version,
                "latest": current,
                "update_type": _update_type(current_v, latest_v),
            }
        )
    return outdated, skipped