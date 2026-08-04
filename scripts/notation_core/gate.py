"""Pre-apply, whole-run verdict.

Only this sees every proposal, so only this can enforce the run-level
no-growth rule. A per-proposal check structurally cannot: three additions that
each pass their band can still leave the gated file bigger.
"""

from . import ledger


def gate(run_id):
    """-> the run verdict. Refuses only when the GATED net is positive."""
    run = ledger.load(run_id)
    buckets = {}
    for p in run["proposals"]:
        b = p.get("bucket", "project")
        buckets[b] = buckets.get(b, 0) + p.get("delta", 0)

    gated_net = sum(
        p.get("delta", 0) for p in run["proposals"] if p.get("gated")
    )

    reasons = []
    if gated_net > 0:
        reasons.append(
            "run adds {} chars to the gated global file across {} proposal(s); "
            "offset it or route the largest into a note".format(
                gated_net, sum(1 for p in run["proposals"] if p.get("gated"))
            )
        )

    return {
        "run_id": run_id,
        "buckets": buckets,
        "gated_net": gated_net,
        "refused": bool(reasons),
        "reasons": reasons,
    }
