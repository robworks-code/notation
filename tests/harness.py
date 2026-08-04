#!/usr/bin/env python3
"""Shared check/report helpers for the notation_core test scripts.

The older test files each define their own copy; they are left alone.
New test files import from here so the pattern is not copied six more times.
"""

import sys

_failures = []


def check(name, condition, detail="", info=""):
    """Print one row. `detail` is FAILURE-only; `info` prints either way."""
    status = "ok  " if condition else "FAIL"
    suffix = info if condition else " - ".join(x for x in (info, detail) if x)
    print("  [{}] {}".format(status, name) + (" - {}".format(suffix) if suffix else ""))
    if not condition:
        _failures.append(name)


def report(label):
    """Print the summary and exit non-zero if anything failed."""
    print()
    if _failures:
        print("{} FAILED: {} check(s)".format(label, len(_failures)))
        for f in _failures:
            print("  - {}".format(f))
        sys.exit(1)
    print("all {} checks passed".format(label))
