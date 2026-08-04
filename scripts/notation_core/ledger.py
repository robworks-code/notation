"""Run-scoped ledger. The gate needs whole-run state; this holds it.

NOTATION_RUNS_DIR overrides the location so tests never touch the real one.
"""

import hashlib
import json
import os

from . import measure


class RunLedgerError(Exception):
    """Base exception for ledger-format errors (JSON or structure)."""
    pass


class RunLedgerJSONError(RunLedgerError):
    """Ledger file exists but contains invalid JSON."""
    pass


class RunLedgerInvalidError(RunLedgerError):
    """Ledger file is valid JSON but is not a valid ledger structure."""
    pass


def runs_dir():
    override = os.environ.get("NOTATION_RUNS_DIR")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(os.path.expanduser("~"), ".claude", "notation-runs")


def _path(run_id):
    return os.path.join(runs_dir(), "{}.json".format(run_id))


def file_hash(path):
    """sha256 of the file's bytes; empty-file digest when it does not exist."""
    h = hashlib.sha256()
    full = os.path.abspath(os.path.expanduser(path))
    if os.path.isfile(full):
        with open(full, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


def _write(run):
    d = runs_dir()
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(_path(run["run_id"]), "w", encoding="utf-8") as fh:
        json.dump(run, fh, indent=2, sort_keys=True)
    return run


def open_run(targets, run_id, now):
    """Record identity plus a pre-run size and hash for every target."""
    recorded = {}
    for t in targets:
        full = os.path.abspath(os.path.expanduser(t))
        recorded[full] = {
            "chars": measure.measure(full)["chars"],
            "sha256": file_hash(full),
        }
    return _write({
        "run_id": run_id,
        "opened_at": now,
        "targets": recorded,
        "proposals": [],
        "closed": False,
    })


def load(run_id):
    """-> the ledger.

    Raises three distinct errors:
    - LookupError if run id was never opened (file does not exist)
    - RunLedgerJSONError if file is not valid JSON
    - RunLedgerInvalidError if JSON is valid but not a valid ledger structure
    """
    p = _path(run_id)
    if not os.path.isfile(p):
        raise LookupError(
            "no ledger for run '{}' at {}; refusing to guess".format(run_id, p)
        )
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        raise RunLedgerJSONError(
            "ledger for run '{}' at {} is not valid JSON: {}".format(run_id, p, e)
        )

    required_keys = {"run_id", "opened_at", "targets", "proposals", "closed"}
    if not isinstance(data, dict) or not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys() if isinstance(data, dict) else [])
        raise RunLedgerInvalidError(
            "ledger for run '{}' is invalid; missing keys: {}".format(run_id, missing)
        )

    return data


def add_proposal(run_id, proposal):
    run = load(run_id)
    run["proposals"].append(proposal)
    return _write(run)
