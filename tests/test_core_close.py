#!/usr/bin/env python3
"""Post-apply reconciliation.

Predicting -1840 and observing -300 means the edit did not land as drafted.
Nothing in notation notices that today because prediction and outcome are never
compared. Tolerance is zero on purpose: any band is a range in which the edit
silently did not land.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import close, ledger


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


with tempfile.TemporaryDirectory() as d:
    os.environ["NOTATION_RUNS_DIR"] = os.path.join(d, "runs")

    print("\ncase: an edit that landed as drafted reconciles")
    t1 = os.path.join(d, "a.md")
    _write(t1, "x" * 1000)
    ledger.open_run([t1], run_id="ok", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("ok", {"delta": -400, "bucket": "global", "gated": True, "target": t1})
    _write(t1, "x" * 600)
    r = close.close("ok")
    check("gap is zero", r["files"][0]["gap"] == 0, info="gap {}".format(r["files"][0]["gap"]))
    check("and the run reconciles", r["reconciled"] is True)
    check("with no findings", r["findings"] == [])

    print("\ncase: an edit that did not land is a finding")
    t2 = os.path.join(d, "b.md")
    _write(t2, "x" * 1000)
    ledger.open_run([t2], run_id="short", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("short", {"delta": -1840, "bucket": "global", "gated": True, "target": t2})
    _write(t2, "x" * 700)          # only -300, not -1840
    r2 = close.close("short")
    check("the gap is reported", r2["files"][0]["gap"] == 1540, info="{}".format(r2["files"][0]["gap"]))
    check("the run does NOT reconcile", r2["reconciled"] is False)
    check("and the file is named", t2 in r2["findings"][0])

    print("\ncase: tolerance is exactly zero")
    t3 = os.path.join(d, "c.md")
    _write(t3, "x" * 100)
    ledger.open_run([t3], run_id="offbyone", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("offbyone", {"delta": -10, "bucket": "global", "gated": True, "target": t3})
    _write(t3, "x" * 91)           # -9, one off
    check("a one-char gap still fails", close.close("offbyone")["reconciled"] is False)

    print("\ncase: an outside edit is reported as drift, not as our delta")
    t4 = os.path.join(d, "d.md")
    _write(t4, "x" * 100)
    ledger.open_run([t4], run_id="drift", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("drift", {"delta": 0, "bucket": "global", "gated": True, "target": t4})
    _write(t4, "y" * 100)          # same size, different content
    r4 = close.close("drift")
    check("same-size content change is flagged as drift", r4["files"][0]["drifted"] is True,
          detail="a size-only check cannot see this")

report("core-close")
