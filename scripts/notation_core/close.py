"""Post-apply reconciliation: did the edit land as drafted?

Two failure modes are reported, and they are deliberately not the same field:

- the LANDING GAP - predicted chars against observed chars, tolerance zero.
- DRIFT - the file changed in a way this run cannot account for.

Drift is answered in three states, never as a boolean. The ledger holds only a
pre-run hash and a predicted char delta, so for a file this run actually wrote
to, a changed hash is consistent with both "only my edit landed" and "my edit
landed and someone else also wrote here". A boolean would have to report False
there, and a False that really means "I could not tell" is the false-zero
pattern this core exists to remove. So:

- 'none'         - the file is byte-identical to its pre-run hash. Certain.
- 'detected'     - the run recorded no proposal for this file, yet its bytes
                   changed. Nothing in the run can explain that. Certain.
- 'undetermined' - the bytes changed and the run did write here. The evidence
                   cannot separate our write from anyone else's, and this says
                   so rather than reporting a reassuring False.
"""

from . import constants, ledger, measure

DRIFT_NONE = "none"
DRIFT_DETECTED = "detected"
DRIFT_UNDETERMINED = "undetermined"


def _drift(path, before_hash, proposal_count):
    """-> (state, reason). See the module docstring for why this is not a bool."""
    if ledger.file_hash(path) == before_hash:
        return DRIFT_NONE, "byte-identical to the pre-run hash"
    if proposal_count == 0:
        return DRIFT_DETECTED, (
            "content differs from the pre-run hash and this run recorded no "
            "proposal for the file, so nothing in the run explains the change"
        )
    return DRIFT_UNDETERMINED, (
        "content differs from the pre-run hash and this run wrote here, so the "
        "run's own write and an outside edit cannot be told apart from a size "
        "and a hash alone"
    )


def close(run_id):
    """-> reconciliation report. Tolerance is zero by design.

    Marks the run closed, and refuses a run that is already closed: a second
    close would re-report a first close's findings as if they were fresh.
    """
    run = ledger.load(run_id)

    predicted = {}
    counts = {}
    for p in run["proposals"]:
        t = p.get("target")
        if t:
            t = measure.norm_path(t)
            predicted[t] = predicted.get(t, 0) + p.get("delta", 0)
            counts[t] = counts.get(t, 0) + 1

    files = []
    findings = []
    for path, before in sorted(run["targets"].items()):
        actual = measure.measure(path)["chars"] - before["chars"]
        want = predicted.get(path, 0)
        gap = abs(actual - want)
        state, reason = _drift(path, before["sha256"], counts.get(path, 0))

        files.append({
            "path": path, "predicted": want, "actual": actual,
            "gap": gap, "drift": state, "drift_reason": reason,
        })
        if gap > constants.RECONCILE_TOLERANCE:
            findings.append(
                "{}: predicted {} chars, observed {} (gap {}) - "
                "the edit did not land as drafted".format(path, want, actual, gap)
            )
        if state == DRIFT_DETECTED:
            findings.append(
                "{}: {} - something edited this file outside the run".format(
                    path, reason
                )
            )

    # A proposal whose target was never registered cannot be reconciled at
    # all. add_proposal refuses those, so this can only fire on a ledger
    # written by an older version - and it must be a finding, not silence.
    for path in sorted(predicted):
        if path not in run["targets"]:
            findings.append(
                "{}: proposals were recorded against this file but it was never "
                "registered as a target, so nothing re-measured it".format(path)
            )

    ledger.mark_closed(run_id)

    # 'undetermined' is the ORDINARY outcome for a file the run wrote to, so
    # it is not a finding - failing every successful run would train a caller
    # to ignore the report. It is surfaced as its own list instead, and the
    # word 'reconciled' is scoped accordingly: gaps closed and no PROVEN
    # drift. A caller that needs certainty about outside edits has to read
    # drift_undetermined, which is why the state is a word and never a bool.
    return {
        "run_id": run_id,
        "files": files,
        "reconciled": not findings,
        "reconciled_means": (
            "every predicted delta was observed exactly and no drift was "
            "proven; files listed in drift_undetermined were not cleared"
        ),
        "drift_undetermined": [
            f["path"] for f in files if f["drift"] == DRIFT_UNDETERMINED
        ],
        "drift_detected": [
            f["path"] for f in files if f["drift"] == DRIFT_DETECTED
        ],
        "findings": findings,
    }
