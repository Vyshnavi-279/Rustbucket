"""License normalization and copyleft conflict detection.

The license lookup table lives in ``scanner/data/licenses.json`` and is
owned by this module alone, so no other team member depends on it.
"""

import json
import os
import re

_SPDX_TO_CATEGORY = None
_SPDX_CANONICAL = None
_RANK = {"permissive": 0, "weak_copyleft": 1, "strong_copyleft": 2, "network_copyleft": 3}
_MAX_FREETEXT_LENGTH = 200

_PROJECT_PERMISSIVE_CATEGORY = "permissive"

_SINGLE_MAP = {
    "mit": "MIT",
    "mit license": "MIT",
    "the mit license": "MIT",
    "expat": "MIT",
    "apache 2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "apache license": "Apache-2.0",
    "apache2": "Apache-2.0",
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "bsd-3": "BSD-3-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "new bsd license": "BSD-3-Clause",
    "modified bsd license": "BSD-3-Clause",
    "bsd 2-clause": "BSD-2-Clause",
    "freebsd license": "BSD-2-Clause",
    "isc license": "ISC",
    "isc": "ISC",
    "unlicense": "Unlicense",
    "cc0": "CC0-1.0",
    "cc0 1.0": "CC0-1.0",
    "zlib license": "Zlib",
    "python software foundation license": "PSF-2.0",
    "python license": "Python-2.0",
    "gplv3": "GPL-3.0-only",
    "gplv2": "GPL-2.0-only",
    "gplv2+": "GPL-2.0-or-later",
    "gpl v3": "GPL-3.0-only",
    "gpl v2": "GPL-2.0-only",
    "gpl-3.0": "GPL-3.0-only",
    "gpl-2.0": "GPL-2.0-only",
    "gpl-3.0+": "GPL-3.0-or-later",
    "gpl-2.0+": "GPL-2.0-or-later",
    "lgplv3": "LGPL-3.0-only",
    "lgplv2.1": "LGPL-2.1-only",
    "agplv3": "AGPL-3.0-only",
    "agplv3+": "AGPL-3.0-or-later",
    "gpl": "GPL-3.0-only",
    "mozilla public license 2.0": "MPL-2.0",
    "mpl": "MPL-2.0",
    "mpl 2.0": "MPL-2.0",
    "eclipse public license 2.0": "EPL-2.0",
    "epl": "EPL-2.0",
}

_CLASSIFIER_SPDX = {
    "mit license": "MIT",
    "apache software license": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "bsd license": "BSD-3-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "bsd 2-clause": "BSD-2-Clause",
    "isc license (iscl)": "ISC",
    "gnu general public license v3 (gplv3)": "GPL-3.0-only",
    "gnu general public license v3 or later (gplv3+)": "GPL-3.0-or-later",
    "gnu general public license v2 (gplv2)": "GPL-2.0-only",
    "gnu general public license v2 or later (gplv2+)": "GPL-2.0-or-later",
    "gnu lesser general public license v3 (lgplv3)": "LGPL-3.0-only",
    "gnu lesser general public license v3 or later (lgplv3+)": "LGPL-3.0-or-later",
    "gnu lesser general public license v2.1 (lgplv2.1)": "LGPL-2.1-only",
    "gnu affero general public license v3 (agplv3)": "AGPL-3.0-only",
    "gnu affero general public license v3 or later (agplv3+)": "AGPL-3.0-or-later",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "mozilla public license 1.1 (mpl 1.1)": "MPL-1.1",
    "eclipse public license 2.0 (epl-2.0)": "EPL-2.0",
    "python software foundation license": "PSF-2.0",
    "zlib/libpng license": "Zlib",
}


def _load_category_map():
    global _SPDX_TO_CATEGORY, _SPDX_CANONICAL
    if _SPDX_TO_CATEGORY is None:
        path = os.path.join(os.path.dirname(__file__), "data", "licenses.json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        _SPDX_TO_CATEGORY = {}
        _SPDX_CANONICAL = {}
        for category, ids in data.items():
            for spdx in ids:
                _SPDX_TO_CATEGORY[spdx] = category
                _SPDX_TO_CATEGORY[spdx.upper()] = category
                _SPDX_CANONICAL[spdx.upper()] = spdx
    return _SPDX_TO_CATEGORY


def _canonical_spdx(spdx):
    _load_category_map()
    return _SPDX_CANONICAL.get((spdx or "").upper())


def category_of(spdx):
    """Return the category for an SPDX id, or ``None`` if unknown."""
    return _load_category_map().get((spdx or "").upper())


def _collapse(expr):
    return re.sub(r"\s+", " ", expr or "").strip()


def _split_top_level(expr, sep):
    parts = []
    current = []
    depth = 0
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif depth == 0 and expr.startswith(sep, i):
            parts.append("".join(current))
            current = []
            i += len(sep)
            continue
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return parts


def _pick_candidate(candidates, most_permissive):
    mapped = [c for c in candidates if c is not None]
    if not mapped:
        return None
    ranks = [_RANK.get(_load_category_map().get(c.upper()), 99) for c in mapped]
    if most_permissive:
        winner = min(zip(ranks, mapped))
    else:
        winner = max(zip(ranks, mapped))
    return winner[1]


def _resolve_expression(expr):
    expr = _collapse(expr)
    while expr.strip().startswith("(") and expr.strip().endswith(")"):
        text = expr.strip()
        depth = 0
        closes_at_end = False
        for i, ch in enumerate(text):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    closes_at_end = i == len(text) - 1
                    break
        if not closes_at_end:
            break
        expr = text[1:-1].strip()
    or_parts = _split_top_level(expr, " OR ")
    if len(or_parts) > 1:
        return _pick_candidate([_resolve_expression(p) for p in or_parts], True)
    and_parts = _split_top_level(expr, " AND ")
    if len(and_parts) > 1:
        return _pick_candidate([_resolve_expression(p) for p in and_parts], False)
    token = expr.strip(" ()")
    return normalize_single(token)


def _classifier_license(classifiers):
    for line in classifiers or []:
        text = str(line)
        if "License ::" not in text:
            continue
        segments = [seg.strip() for seg in text.split("::") if seg.strip()]
        if not segments:
            continue
        tail = " ".join(segments[1:]).lower().strip(" .")
        for pattern, spdx in _CLASSIFIER_SPDX.items():
            if tail == pattern or pattern in tail:
                return spdx
    return None


def normalize_single(raw):
    """Map a single (non-expression) license string to an SPDX id or ``None``."""
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        for item in raw:
            result = normalize_single(item)
            if result:
                return result
        return None
    if isinstance(raw, dict):
        raw = raw.get("type") or raw.get("spdx_id")
    key = _collapse(str(raw)).lower().strip(" .\"'")
    if not key:
        return None
    key = re.sub(r"\s+", " ", key)
    if key in _SINGLE_MAP:
        return _SINGLE_MAP[key]
    spdx = key.upper()
    canonical = _canonical_spdx(spdx)
    if canonical:
        return canonical
    return None


def normalize_license(raw, classifiers=None):
    """Map arbitrary license strings to an SPDX id, or ``None``.

    PyPI often leaves ``info.license`` empty or pastes the whole license
    text; in those cases the ``License ::`` classifiers are used instead.
    SPDX expressions resolve to a single id: the most permissive option
    for ``OR``, the most restrictive option for ``AND``.
    """
    if classifiers:
        inexpressive = (
            raw is None
            or not _collapse(str(raw))
            or len(_collapse(str(raw))) > _MAX_FREETEXT_LENGTH
        )
        if inexpressive:
            from_classifiers = _classifier_license(classifiers)
            if from_classifiers:
                return from_classifiers
            if raw is None or not _collapse(str(raw)):
                return None
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        for item in raw:
            parsed = normalize_license(item, classifiers=None)
            if parsed:
                return parsed
        return None
    text = _collapse(str(raw))
    if len(text) > _MAX_FREETEXT_LENGTH:
        return None
    if " OR " in text.upper() or " AND " in text.upper() or text.startswith("("):
        return _resolve_expression(text.upper())
    resolved = normalize_single(raw)
    if resolved is None and classifiers:
        return _classifier_license(classifiers)
    return resolved


def _project_is_permissive(project_license):
    spdx = normalize_license(project_license)
    return _load_category_map().get((spdx or "").upper()) == _PROJECT_PERMISSIVE_CATEGORY


def check_licenses(deps, registry_info, project_license=None):
    """Detect license conflicts between dependencies and the project.

    Rules (Section 2.4 of the work plan):
      * permissive project   -> flag strong_copyleft and network_copyleft deps
      * unknown/no project   -> flag only network_copyleft (AGPL)
      * unmappable dep       -> flag with category "unknown"
    """
    issues = []
    project_permissive = _project_is_permissive(project_license)
    for dep in deps:
        info = registry_info.get((dep["ecosystem"], dep["name"]))
        dep_license = None
        if info:
            raw = info.get("license")
            if len(_collapse(str(raw))) > _MAX_FREETEXT_LENGTH:
                raw = None
            dep_license = normalize_license(raw, classifiers=info.get("license_classifiers"))
        if not dep_license:
            issues.append(
                {
                    "package": dep["name"],
                    "license": None,
                    "category": "unknown",
                    "reason": "License could not be determined, review manually",
                }
            )
            continue
        category = _load_category_map().get(dep_license.upper())
        if not category:
            issues.append(
                {
                    "package": dep["name"],
                    "license": dep_license,
                    "category": "unknown",
                    "reason": f"License {dep_license} could not be classified, review manually",
                }
            )
            continue
        if category in ("strong_copyleft", "network_copyleft") and project_permissive:
            issues.append(
                {
                    "package": dep["name"],
                    "license": dep_license,
                    "category": category,
                    "reason": (
                        f"{dep_license} is a {category.replace('_', ' ')} license "
                        f"in a permissive ({normalize_license(project_license)}) project"
                    ),
                }
            )
        elif category == "network_copyleft" and not project_permissive:
            issues.append(
                {
                    "package": dep["name"],
                    "license": dep_license,
                    "category": category,
                    "reason": (
                        f"{dep_license} is a network copyleft license and the project "
                        "license could not be verified"
                    ),
                }
            )
    return issues