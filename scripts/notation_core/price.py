"""Signed, bucketed deltas. Both sides are measured; neither is estimated."""

import os

from . import measure


def _chars(path):
    if path is None:
        return None
    full = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(full):
        return 0
    return len(measure.read_text(full))


def price(removed_path, added_path, target):
    """-> signed delta for one proposal, bucketed by its target file.

    added_path is required. The budget rules say draft the replacement before
    quoting a number; refusing here is what keeps a guess from entering the
    ledger looking like a measurement.
    """
    if added_path is None:
        raise ValueError(
            "price requires a drafted replacement; "
            "a delta without one is an estimate, not a measurement"
        )
    removed_chars = _chars(removed_path) or 0
    added_chars = _chars(added_path) or 0
    bucket = measure.resolve_bucket(target)
    return {
        "removed_chars": removed_chars,
        "added_chars": added_chars,
        "delta": added_chars - removed_chars,
        "bucket": bucket,
        "gated": measure.is_gated(bucket),
    }
