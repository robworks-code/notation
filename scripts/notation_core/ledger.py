"""Run-scoped ledger. The gate needs whole-run state; this holds it.

NOTATION_RUNS_DIR overrides the location so tests never touch the real one.

Every refusal is catchable as RunLedgerError:
- RunLedgerMissingError: run id was never opened (file does not exist)
- RunLedgerJSONError: file exists but is not valid JSON
- RunLedgerInvalidError: JSON is valid but not a valid ledger structure
- RunLedgerExistsError: opening an id that already has a ledger
- RunLedgerClosedError: adding to, or re-closing, a closed run
- RunLedgerUnregisteredTargetError: a proposal names an unregistered file

RunLedgerMissingError inherits from both RunLedgerError and LookupError, so
existing code catching LookupError continues to work while also allowing
unified handling of all three refusals via the RunLedgerError base.
"""

import hashlib
import json
import os

from . import measure


class RunLedgerError(Exception):
    """Base exception for all ledger-loading refusals."""
    pass


class RunLedgerMissingError(RunLedgerError, LookupError):
    """Run id was never opened (file does not exist).

    Inherits from both RunLedgerError and LookupError for backward
    compatibility: existing `except LookupError` handlers still work,
    and all three refusals are now catchable via `except RunLedgerError`.
    """
    pass


class RunLedgerJSONError(RunLedgerError):
    """Ledger file exists but contains invalid JSON."""
    pass


class RunLedgerInvalidError(RunLedgerError):
    """Ledger file is valid JSON but is not a valid ledger structure."""
    pass


class RunLedgerExistsError(RunLedgerError):
    """A ledger for this run id already exists, so opening it would clobber it.

    A second open on a live run id used to write a fresh ledger with an empty
    proposal list, which discarded every proposal the first open had collected
    and left the whole-run gate reporting a clean net of zero. Shell state does
    not survive a session's Bash calls, so a re-open is an ordinary accident -
    a retry, a re-read of the doc, two sessions inventing the same id - and it
    must be refused for the same reason a stale ledger is refused: the core
    never repairs run state it cannot reconstruct.
    """
    pass


class RunLedgerClosedError(RunLedgerError):
    """The run is already closed, so it can no longer be added to or re-closed."""
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
    full = measure.norm_path(path)
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


def find_target(run, path):
    """-> the registered key this path refers to, or None.

    The exact normalized spelling is tried first. Only if that misses does it
    compare fully resolved paths, which is what lets a target opened by a
    relative path (resolved through a cwd the OS reports with its symlinks
    already expanded) match the same file later named absolutely. This is a
    LOOKUP fallback only - it never decides scope, which stays a question
    about the name the caller used (see measure.resolve_bucket).
    """
    full = measure.norm_path(path)
    if full in run["targets"]:
        return full
    real = os.path.realpath(full)
    for key in run["targets"]:
        if os.path.realpath(key) == real:
            return key
    return None


def _record(path):
    return {
        "chars": measure.measure(path)["chars"],
        "sha256": file_hash(path),
    }


def open_run(targets, run_id, now):
    """Record identity plus a pre-run size and hash for every target.

    Refuses an id that already has a ledger. See RunLedgerExistsError.
    """
    p = _path(run_id)
    if os.path.exists(p):
        raise RunLedgerExistsError(
            "run '{}' already has a ledger at {}; refusing to reopen it, "
            "because a fresh ledger would discard the proposals already "
            "recorded and the gate would then see a net of zero. Mint a new "
            "run id, or use 'register' to add a target to the run in "
            "progress".format(run_id, p)
        )
    recorded = {}
    for t in targets:
        recorded[measure.norm_path(t)] = _record(t)
    return _write({
        "run_id": run_id,
        "opened_at": now,
        "targets": recorded,
        "proposals": [],
        "closed": False,
    })


def register_target(run_id, target):
    """Add a target to a run already open, with its own pre-run size and hash.

    Every file a run will touch has to be on the ledger before the writes, or
    close() cannot reconcile it - and an unreconciled file is exactly where a
    relocation loses content: the removal reconciles, the append silently
    fails, and the run reports success. Registering an already-registered
    target is a no-op that keeps the ORIGINAL pre-run record, so calling this
    twice can never reset the baseline drift is measured against.
    """
    run = load(run_id)
    if run["closed"]:
        raise RunLedgerClosedError(
            "run '{}' is already closed; it cannot take new targets".format(run_id)
        )
    existing = find_target(run, target)
    if existing is not None:
        return {"run_id": run_id, "target": existing, "registered": False,
                "already_registered": True}
    full = measure.norm_path(target)
    run["targets"][full] = _record(full)
    _write(run)
    return {"run_id": run_id, "target": full, "registered": True,
            "already_registered": False}


def mark_closed(run_id):
    """Flip the ledger's `closed` flag. Refuses a run that is already closed."""
    run = load(run_id)
    if run["closed"]:
        raise RunLedgerClosedError(
            "run '{}' was already closed; its reconciliation has already been "
            "reported once and re-running close would report it again as if "
            "it were the first".format(run_id)
        )
    run["closed"] = True
    _write(run)
    return run


def load(run_id):
    """-> the ledger.

    Raises one of three RunLedgerError subtypes:
    - RunLedgerMissingError if run id was never opened (file does not exist)
      (also catchable as LookupError for backward compatibility)
    - RunLedgerJSONError if file is not valid JSON
    - RunLedgerInvalidError if JSON is valid but not a valid ledger structure

    All three are catchable via `except RunLedgerError`.
    """
    p = _path(run_id)
    if not os.path.isfile(p):
        raise RunLedgerMissingError(
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


class RunLedgerUnregisteredTargetError(RunLedgerError):
    """A proposal names a file the run never registered as a target.

    This is what makes 'register every file the run will touch' structural
    rather than merely documented: an unregistered target is refused at the
    moment the proposal is recorded - before any write - instead of going
    unreconciled at close, where a silently failed append reads as success.
    """
    pass


def add_proposal(run_id, proposal):
    """Append one priced proposal. Its target must already be registered."""
    run = load(run_id)
    if run["closed"]:
        raise RunLedgerClosedError(
            "run '{}' is already closed; it cannot take new proposals".format(run_id)
        )
    target = proposal.get("target")
    if target is not None:
        full = find_target(run, target)
        if full is None:
            full = measure.norm_path(target)
            raise RunLedgerUnregisteredTargetError(
                "run '{}' has no registered target '{}'; close() reconciles only "
                "registered targets, so recording this proposal would leave the "
                "file unchecked. Register it first: "
                "register --run-id {} --target {}".format(
                    run_id, full, run_id, full
                )
            )
        proposal = dict(proposal)
        proposal["target"] = full
    run["proposals"].append(proposal)
    return _write(run)
