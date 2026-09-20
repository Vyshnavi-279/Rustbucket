from scanner.score import build_summary, compute_score

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


def _summary(critical=0, high=0, medium=0, low=0, outdated=0, license_issues=0, total=0):
    return {
        "total_dependencies": total,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "outdated": outdated,
        "license_issues": license_issues,
    }


def _vuln(severity):
    return {"package": "p", "severity": severity}


class TestComputeScore:
    def test_no_findings_is_100(self):
        assert compute_score(_summary(), 0) == 100

    def test_one_critical_is_85(self):
        assert compute_score(_summary(critical=1), 0) == 85

    def test_five_criticals_hits_cap(self):
        assert compute_score(_summary(critical=5), 0) == 40

    def test_four_criticals_hits_cap_exactly(self):
        assert compute_score(_summary(critical=4), 0) == 40

    def test_never_below_zero(self):
        counts = _summary(critical=10, high=10, medium=10, low=10, outdated=10, license_issues=5)
        assert compute_score(counts, 10) == 0

    def test_three_major_outdated_is_94(self):
        assert compute_score(_summary(), 3) == 94

    def test_five_major_outdated_hits_cap(self):
        assert compute_score(_summary(), 5) == 90

    def test_two_license_issues_is_80(self):
        assert compute_score(_summary(license_issues=2), 0) == 80

    def test_high_cap(self):
        assert compute_score(_summary(high=3), 0) == 76
        assert compute_score(_summary(high=4), 0) == 70

    def test_medium_cap(self):
        assert compute_score(_summary(medium=5), 0) == 85
        assert compute_score(_summary(medium=6), 0) == 85

    def test_low_cap(self):
        assert compute_score(_summary(low=5), 0) == 95
        assert compute_score(_summary(low=6), 0) == 95


class TestBuildSummary:
    def test_counts_vulnerabilities_by_severity(self):
        deps = [{"name": "a"}, {"name": "b"}]
        vulns = [_vuln(CRITICAL), _vuln(HIGH), _vuln(HIGH), _vuln(LOW)]
        summary = build_summary(deps, vulns, ["o1"], ["l1"])
        assert summary == {
            "total_dependencies": 2,
            "critical": 1,
            "high": 2,
            "medium": 0,
            "low": 1,
            "outdated": 1,
            "license_issues": 1,
        }