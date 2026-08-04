"""Post-apply reconciliation: did the edit land as drafted?"""

from . import constants, ledger, measure


def close(run_id):
    """-> reconciliation report. Tolerance is zero by design."""
    run = ledger.load(run_id)

    predicted = {}
    for p in run["proposals"]:
        t = p.get("target")
        if t:
            predicted[t] = predicted.get(t, 0) + p.get("delta", 0)

    files = []
    findings = []
    for path, before in sorted(run["targets"].items()):
        actual = measure.measure(path)["chars"] - before["chars"]
        want = predicted.get(path, 0)
        gap = abs(actual - want)
        drifted = (
            gap == 0
            and actual == 0
            and ledger.file_hash(path) != before["sha256"]
        )
        files.append({
            "path": path, "predicted": want, "actual": actual,
            "gap": gap, "drifted": drifted,
        })
        if gap > constants.RECONCILE_TOLERANCE:
            findings.append(
                "{}: predicted {} chars, observed {} (gap {}) - "
                "the edit did not land as drafted".format(path, want, actual, gap)
            )
        elif drifted:
            findings.append(
                "{}: size unchanged but content differs from the pre-run hash - "
                "something edited this file outside the run".format(path)
            )

    return {
        "run_id": run_id,
        "files": files,
        "reconciled": not findings,
        "findings": findings,
    }
