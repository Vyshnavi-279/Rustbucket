from scanner.outdated import check_outdated


def _registry_info(*pairs):
    info = {}
    for ecosystem, name, latest in pairs:
        info[(ecosystem, name)] = {"latest": latest, "license": None, "license_classifiers": []}
    return info


def _dep(name, version, ecosystem="npm"):
    return {"name": name, "version": version, "ecosystem": ecosystem}


def test_major_update():
    deps = [_dep("express", "4.16.0")]
    info = _registry_info(("npm", "express", "5.0.0"))
    outdated, _ = check_outdated(deps, info)
    assert outdated == [
        {"package": "express", "current": "4.16.0", "latest": "5.0.0", "update_type": "major"}
    ]


def test_minor_update():
    deps = [_dep("express", "4.16.0")]
    info = _registry_info(("npm", "express", "4.19.0"))
    outdated, _ = check_outdated(deps, info)
    assert outdated[0]["update_type"] == "minor"


def test_patch_update():
    deps = [_dep("express", "4.16.0")]
    info = _registry_info(("npm", "express", "4.16.2"))
    outdated, _ = check_outdated(deps, info)
    assert outdated[0]["update_type"] == "patch"


def test_up_to_date_skipped():
    deps = [_dep("express", "4.16.0")]
    info = _registry_info(("npm", "express", "4.16.0"))
    outdated, _ = check_outdated(deps, info)
    assert outdated == []


def test_unknown_version_skipped():
    deps = [_dep("express", "unknown")]
    info = _registry_info(("npm", "express", "5.0.0"))
    outdated, skipped = check_outdated(deps, info)
    assert outdated == []
    assert skipped == 1


def test_pre_release_not_confused_with_newer():
    deps = [_dep("react", "16.13.0")]
    info = _registry_info(("npm", "react", "19.0.0-rc.1"))
    outdated, _ = check_outdated(deps, info)
    assert outdated[0]["update_type"] == "major"


def test_registry_down_is_skipped_not_crash():
    deps = [_dep("express", "4.16.0")]
    outdated, _ = check_outdated(deps, {})
    assert outdated == []


def test_unparseable_version_skipped():
    deps = [_dep("thing", "not-a-version")]
    info = _registry_info(("npm", "thing", "1.0.0"))
    outdated, skipped = check_outdated(deps, info)
    assert outdated == []
    assert skipped == 1


def test_pypi_and_npm_same_name_are_distinct():
    deps = [_dep("flask", "1.1.2", "pypi"), _dep("flask", "1.0.0", "npm")]
    info = _registry_info(("pypi", "flask", "2.3.0"), ("npm", "flask", "1.3.1"))
    outdated, _ = check_outdated(deps, info)
    assert len(outdated) == 2
    kinds = {(o["current"], o["latest"]) for o in outdated}
    assert ("1.1.2", "2.3.0") in kinds
    assert ("1.0.0", "1.3.1") in kinds