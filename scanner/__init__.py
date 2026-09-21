"""Rustbucket scanning engine.

The public entry point is ``run_scan(deps, project_license=None)`` which
Person 1's worker calls with the Section 2.3 dependency list and returns
the Section 2.4 scan result.
"""

from scanner.core import run_scan
from scanner.errors import ScanError

__all__ = ["ScanError", "run_scan"]