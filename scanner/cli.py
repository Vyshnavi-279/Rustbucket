"""Command-line runner: ``python -m scanner.cli <deps.json> [--license SPDX]``"""

import argparse
import json
import sys

from scanner.core import run_scan
from scanner.errors import ScanError


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="scanner",
        description="Rustbucket scanning engine: report CVEs, outdated packages "
        "and license conflicts for a dependency list.",
    )
    parser.add_argument("file", help="path to a JSON dependency list (Section 2.3)")
    parser.add_argument("--license", default=None, help="project SPDX license, e.g. MIT")
    args = parser.parse_args(argv)

    with open(args.file, encoding="utf-8") as fh:
        deps = json.load(fh)

    try:
        result = run_scan(deps, args.license)
    except ScanError as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())