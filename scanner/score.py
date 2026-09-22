"""Health score calculation, implemented exactly to Section 2.6.

Weights and per-category caps live in one constants block so they are
easy to explain in the demo.
"""

from collections import Counter

WEIGHTS = {
    "critical": (15, 60),
    "high": (8, 30),
    "medium": (3, 15),
    "low": (1, 5),
    "outdated_major": (2, 10),
    "license_issues": (10, 20),
}


def build_summary(deps, vulns, outdated, license_issues):
    """Return the summary object of Section 2.4."""
    severity_counts = Counter(v.get("severity") for v in vulns)
    return {
        "total_dependencies": len(deps),
        "critical": severity_counts.get("CRITICAL", 0),
        "high": severity_counts.get("HIGH", 0),
        "medium": severity_counts.get("MEDIUM", 0),
        "low": severity_counts.get("LOW", 0),
        "outdated": len(outdated),
        "license_issues": len(license_issues),
    }


def compute_score(summary_counts, major_outdated_count):
    """Compute the 0-100 health score using the shared formula."""
    critical, high, medium, low = (
        summary_counts.get("critical", 0),
        summary_counts.get("high", 0),
        summary_counts.get("medium", 0),
        summary_counts.get("low", 0),
    )
    license_issues = summary_counts.get("license_issues", 0)
    score = 100
    for count, (weight, cap) in [
        (critical, WEIGHTS["critical"]),
        (high, WEIGHTS["high"]),
        (medium, WEIGHTS["medium"]),
        (low, WEIGHTS["low"]),
    ]:
        score -= min(weight * count, cap)
    score -= min(WEIGHTS["outdated_major"][0] * major_outdated_count, WEIGHTS["outdated_major"][1])
    score -= min(WEIGHTS["license_issues"][0] * license_issues, WEIGHTS["license_issues"][1])
    return max(0, min(100, round(score)))