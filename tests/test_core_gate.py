#!/usr/bin/env python3
"""The whole-run gate.

Three individually legal additions can still blow the budget, which is exactly
what a per-proposal check cannot see. Only the run-level view can refuse that.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import gate, ledger

with tempfile.TemporaryDirectory() as d:
    os.environ["NOTATION_RUNS_DIR"] = os.path.join(d, "runs")
    target = os.path.join(d, "CLAUDE.md")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("x\n")

    print("\ncase: a net reduction passes")
    ledger.open_run([target], run_id="pass", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("pass", {"delta": -1840, "bucket": "global", "gated": True})
    ledger.add_proposal("pass", {"delta": 118, "bucket": "global", "gated": True})
    v = gate.gate("pass")
    check("net is the sum", v["gated_net"] == -1722, info="{}".format(v["gated_net"]))
    check("and it is not refused", v["refused"] is False)

    print("\ncase: three legal additions still blow the budget")
    ledger.open_run([target], run_id="creep", now="2026-08-04T00:00:00Z")
    for _ in range(3):
        ledger.add_proposal("creep", {"delta": 150, "bucket": "global", "gated": True})
    v2 = gate.gate("creep")
    check("net growth is caught", v2["gated_net"] == 450)
    check("the run is refused", v2["refused"] is True,
          detail="each proposal is under INLINE_MAX; only the run view sees this")
    check("and says why", bool(v2["reasons"]), detail="a refusal with no reason is unactionable")

    print("\ncase: ungated buckets never refuse")
    ledger.open_run([target], run_id="notes-only", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("notes-only", {"delta": 9000, "bucket": "notes", "gated": False})
    v3 = gate.gate("notes-only")
    check("notes growth is reported", v3["buckets"]["notes"] == 9000)
    check("but does not feed the gate", v3["gated_net"] == 0)
    check("and does not refuse", v3["refused"] is False)

    print("\ncase: a project target is advisory, never refused")
    ledger.open_run([target], run_id="proj", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("proj", {"delta": 5000, "bucket": "project", "gated": False})
    v4 = gate.gate("proj")
    check("project growth is reported", v4["buckets"]["project"] == 5000)
    check("and never refused", v4["refused"] is False)

    print("\ncase: a missing ledger refuses to guess, it does not pass")
    try:
        gate.gate("never-opened")
        check("missing ledger raises rather than returning a verdict", False,
              detail="a caller that treats 'no exception' as pass would silently permit a global write")
    except ledger.RunLedgerError:
        check("missing ledger raises rather than returning a verdict", True)

report("core-gate")
