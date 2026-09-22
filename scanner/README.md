# Rustbucket Scanner

The scanning & analysis engine for Rustbucket. One Python function,
`run_scan`, takes the shared dependency list (Section 2.3 of the work
plan) and returns the full scan result (Section 2.4): known CVEs,
outdated packages, license conflicts and a 0-100 health score.

## What each module does

| Module            | Responsibility                                                        |
| ----------------- | --------------------------------------------------------------------- |
| `cves.py`         | CVE scan via Trivy; falls back to the OSV.dev API if Trivy is missing |
| `registry.py`     | npm / PyPI registry lookups (latest version + license), concurrent    |
| `outdated.py`     | compare installed vs latest versions → `{current, latest, update_type}` |
| `licenses.py`     | normalize license strings to SPDX ids and detect copyleft conflicts   |
| `score.py`        | the Section 2.6 health score formula and summary counts               |
| `core.py`         | `run_scan()` orchestration: validation, parallel CVE + registry work  |
| `errors.py`       | `ScanError`, the single exception the caller must handle              |
| `cli.py`          | `python -m scanner.cli` command-line runner (for standalone testing)  |
| `data/licenses.json` | SPDX id → category lookup table (permissive, weak/strong/network copyleft) |

## How scoring works

The score starts at 100 and deducts points per finding, capped per
category (weights and caps live in one block at the top of `score.py`):

| Finding         | Deduction | Cap  |
| --------------- | --------- | ---- |
| critical CVE    | 15 each   | 60   |
| high CVE        | 8 each    | 30   |
| medium CVE      | 3 each    | 15   |
| low CVE         | 1 each    | 5    |
| major outdated  | 2 each    | 10   |
| license issue   | 10 each   | 20   |

The result is clamped to 0-100 and rounded to an integer.

## How to run the CLI

```bash
pip install -r scanner/requirements.txt

python -m scanner.cli scanner/samples/vulnerable_py.json --license MIT
```

Each sample input lives in `scanner/samples/`; the saved outputs next to
them are hand-checked examples. `small_npm.json`, `vulnerable_py.json`,
`medium_mixed.json` and `license_conflict.json`.

The CVE scan uses a local `trivy` binary when present (set
`TRIVY_CACHE_DIR` to control where the vulnerability database is stored)
and automatically falls back to `api.osv.dev` otherwise, adding the
warning `"Trivy unavailable, used OSV.dev"`.

## Tests

```bash
ruff check scanner
pytest scanner -m "not network"   # no internet, no trivy binary needed
```

Tests that need the real internet or the Trivy binary are marked
`@pytest.mark.network` (registered in `scanner/pytest.ini`), so CI can
run everything else with no internet. The captured Trivy JSON fixture in
`scanner/tests/fixtures/` lets the CVE parsing tests run without the
binary.