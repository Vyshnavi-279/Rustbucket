# Sample dependency lists

Hand-written inputs for exercising the engine without any other team
member. Each `<name>.json` is the input (Section 2.3 dependency list);
the matching `<name>.output.json` is the real result saved from a run
with a warm Trivy database.

| Sample                  | Input                                | Run with          |
| ----------------------- | ------------------------------------ | ----------------- |
| `small_npm.json`        | 5 npm packages                       | —                 |
| `vulnerable_py.json`    | old Django/Flask/Jinja2/Requests/…   | —                 |
| `medium_mixed.json`     | 30 packages, npm + pypi              | `--license MIT`   |
| `license_conflict.json` | pylint (GPL) in an MIT project       | `--license MIT`   |

## What the saved outputs show

* `vulnerable_py` – real CVEs for `django==2.2.0` (SQL injection,
  account takeover, …), several outdated packages, score 0.
* `small_npm` – `lodash 4.17.15` and friends report CVEs; every package
  is outdated (`express` major, …).
* `medium_mixed` – 30 real packages scanned end to end; all outdated,
  high/medium CVE counts populated.
* `license_conflict` – inspite of an MIT project license, `pylint`
  (`GPL-2.0-or-later`, strong copyleft) is flagged, with no false
  "unknown" license entries.

## Run time

Measured on a laptop with a warm Trivy database:

| Sample             | Dependencies | Wall clock |
| ------------------ | ------------ | ---------- |
| `small_npm`        | 5            | ~0.7 s     |
| `vulnerable_py`    | 6            | ~0.5 s     |
| `license_conflict` | 6            | ~0.3 s     |
| `medium_mixed`     | 30           | ~3.1 s     |

Target is under 60 seconds for 50 dependencies; 30 dependencies finish
in about 3 seconds, so the target is comfortably met. Registry lookups
run concurrently (10 workers) and the Trivy database is local after the
first download.

## Reproduce

From the repository root, with `trivy` and the scanner requirements
installed:

```bash
python -m scanner.cli scanner/samples/vulnerable_py.json
python -m scanner.cli scanner/samples/license_conflict.json --license MIT
```

If the `trivy` binary is not on `PATH`, the run still succeeds using the
OSV.dev fallback and adds the warning `"Trivy unavailable, used OSV.dev"`.