import pytest

from scanner.licenses import (
    category_of,
    check_licenses,
    normalize_license,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("MIT", "MIT"),
        ("MIT License", "MIT"),
        ("The MIT License", "MIT"),
        ("Apache 2.0", "Apache-2.0"),
        ("Apache-2.0", "Apache-2.0"),
        ("Apache License 2.0", "Apache-2.0"),
        ("Apache Software License", "Apache-2.0"),
        ("GPLv3", "GPL-3.0-only"),
        ("GPLv2", "GPL-2.0-only"),
        ("GPLv2+", "GPL-2.0-or-later"),
        ("GPL-2.0+", "GPL-2.0-or-later"),
        ("GPL-3.0", "GPL-3.0-only"),
        ("BSD", "BSD-3-Clause"),
        ("BSD-3-Clause", "BSD-3-Clause"),
        ("BSD 3-Clause", "BSD-3-Clause"),
        ("ISC", "ISC"),
        ("Unlicense", "Unlicense"),
        ("CC0-1.0", "CC0-1.0"),
        ("CC0 1.0", "CC0-1.0"),
        ("Zlib", "Zlib"),
        ("PSF-2.0", "PSF-2.0"),
        ("LGPL-3.0-only", "LGPL-3.0-only"),
        ("LGPLv3", "LGPL-3.0-only"),
        ("MPL-2.0", "MPL-2.0"),
        ("EPL-2.0", "EPL-2.0"),
        ("CDDL-1.0", "CDDL-1.0"),
        ("AGPL-3.0-or-later", "AGPL-3.0-or-later"),
        ("gpl-3.0-only", "GPL-3.0-only"),
        ("AGPLv3", "AGPL-3.0-only"),
        (None, None),
        ("", None),
        ("   ", None),
        ("What the heck", None),
        ("made-up-license-9", None),
        ({"type": "MIT"}, "MIT"),
        (["MIT"], "MIT"),
    ],
)
def test_normalize_license_singles(raw, expected):
    assert normalize_license(raw) == expected


def test_normalize_license_whole_license_text_is_none():
    long_text = ("BSD 3-Clause License. Copyright (c) 2022 Someone. " * 8)
    assert normalize_license(long_text) is None


def test_normalize_license_uses_classifiers_for_long_license():
    long_text = "MIT License " * 50
    classifiers = ["License :: OSI Approved :: MIT License"]
    assert normalize_license(long_text, classifiers=classifiers) == "MIT"


def test_normalize_license_uses_classifiers_when_empty():
    classifiers = ["License :: OSI Approved :: BSD License"]
    assert normalize_license("", classifiers=classifiers) == "BSD-3-Clause"
    assert normalize_license(None, classifiers=classifiers) == "BSD-3-Clause"


def test_normalize_license_ignores_length_only_for_with_classifiers():
    assert normalize_license("GPL-3.0-only", classifiers=["License :: OSI Approved :: MIT License"]) == "GPL-3.0-only"


def test_normalize_license_uses_classifiers_when_string_unmappable():
    classifiers = ["License :: OSI Approved :: BSD License"]
    assert normalize_license("Dual License", classifiers=classifiers) == "BSD-3-Clause"


def test_or_expression_prefers_permissive():
    assert normalize_license("MIT OR GPL-3.0-only") == "MIT"
    assert normalize_license("(Apache-2.0 OR GPL-2.0-only)") == "Apache-2.0"


def test_and_expression_prefers_restrictive():
    assert normalize_license("MIT AND GPL-3.0-only") == "GPL-3.0-only"
    assert normalize_license("MIT AND AGPL-3.0-only") == "AGPL-3.0-only"


def test_nested_expression():
    assert normalize_license("(MIT OR Apache-2.0) AND AGPL-3.0-only") == "AGPL-3.0-only"


def test_expression_with_unmappable_part():
    assert normalize_license("MIT OR FANCY-99") == "MIT"


def test_category_of():
    assert category_of("MIT") == "permissive"
    assert category_of("GPL-3.0-only") == "strong_copyleft"
    assert category_of("AGPL-3.0-only") == "network_copyleft"
    assert category_of("LGPL-2.1-only") == "weak_copyleft"
    assert category_of("made-up") is None


def _registry(info_by_key):
    result = {}
    for key, value in info_by_key.items():
        result[key] = {"latest": "1.0.0", "license": value, "license_classifiers": []}
    return result


def test_conflict_strong_copyleft_in_permissive_project():
    deps = [{"name": "pylint", "version": "2.0.0", "ecosystem": "pypi"}]
    info = _registry({("pypi", "pylint"): "GPL-2.0-only"})
    issues = check_licenses(deps, info, "MIT")
    assert len(issues) == 1
    assert issues[0]["category"] == "strong_copyleft"
    assert issues[0]["package"] == "pylint"
    assert issues[0]["license"] == "GPL-2.0-only"
    assert "permissive" in issues[0]["reason"]


def test_conflict_network_copyleft_in_permissive_project():
    deps = [{"name": "mongoengine", "version": "0.0.1", "ecosystem": "pypi"}]
    info = _registry({("pypi", "mongoengine"): "AGPL-3.0-only"})
    issues = check_licenses(deps, info, "Apache-2.0")
    assert issues[0]["category"] == "network_copyleft"


def test_no_conflict_permissive_dependency():
    deps = [{"name": "requests", "version": "1.0.0", "ecosystem": "pypi"}]
    info = _registry({("pypi", "requests"): "Apache-2.0"})
    assert check_licenses(deps, info, "MIT") == []


def test_unknown_project_flags_only_network_copyleft():
    deps = [
        {"name": "agpl-pkg", "version": "1.0.0", "ecosystem": "pypi"},
        {"name": "gpl-pkg", "version": "1.0.0", "ecosystem": "pypi"},
    ]
    info = _registry(
        {
            ("pypi", "agpl-pkg"): "AGPL-3.0-or-later",
            ("pypi", "gpl-pkg"): "GPL-3.0-only",
        }
    )
    issues = check_licenses(deps, info, None)
    assert len(issues) == 1
    assert issues[0]["package"] == "agpl-pkg"
    assert issues[0]["category"] == "network_copyleft"


def test_missing_license_flagged_unknown():
    deps = [{"name": "mystery", "version": "1.0.0", "ecosystem": "npm"}]
    info = _registry({("npm", "mystery"): "Some weird license string"})
    issues = check_licenses(deps, info, "MIT")
    assert len(issues) == 1
    assert issues[0]["category"] == "unknown"
    assert issues[0]["reason"] == "License could not be determined, review manually"


def test_license_via_classifiers_is_picked_up():
    deps = [{"name": "django", "version": "2.2.0", "ecosystem": "pypi"}]
    info = {
        ("pypi", "django"): {
            "latest": "1.0.0",
            "license": "BSD-3-Clause",
            "license_classifiers": ["License :: OSI Approved :: BSD License"],
        }
    }
    assert check_licenses(deps, info, "MIT") == []


def test_license_map_categories_complete():
    from scanner.licenses import _load_category_map

    mapping = _load_category_map()
    assert {"permissive", "weak_copyleft", "strong_copyleft", "network_copyleft"} == set(mapping.values())
    for required in ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD",
                     "Unlicense", "CC0-1.0", "Zlib", "PSF-2.0", "Python-2.0",
                     "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only", "LGPL-3.0-or-later",
                     "MPL-2.0", "EPL-2.0", "CDDL-1.0",
                     "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later",
                     "AGPL-3.0-only", "AGPL-3.0-or-later"]:
        assert required in mapping