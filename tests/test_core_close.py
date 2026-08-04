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
    check("and the file is named",
          bool(r2["findings"]) and t2 in r2["findings"][0],
          detail="findings was empty, nothing to index")

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

    print("\ncase: the four reconciliation states are independently distinguishable")
    print("  -> a caller must be able to tell gap and drift apart, including both at once")

    # state: clean - edit landed exactly, no outside touch
    t5 = os.path.join(d, "e-clean.md")
    _write(t5, "x" * 1000)
    ledger.open_run([t5], run_id="state-clean", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("state-clean", {"delta": -400, "bucket": "global", "gated": True, "target": t5})
    _write(t5, "x" * 600)
    f5 = close.close("state-clean")["files"][0]
    check("clean: gap is zero", f5["gap"] == 0, info="gap {}".format(f5["gap"]))
    check("clean: not drifted", f5["drifted"] is False)

    # state: gap-only - edit did not land, no outside touch
    t6 = os.path.join(d, "f-gap-only.md")
    _write(t6, "x" * 1000)
    ledger.open_run([t6], run_id="state-gap", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("state-gap", {"delta": -1840, "bucket": "global", "gated": True, "target": t6})
    _write(t6, "x" * 700)          # only -300, not -1840
    f6 = close.close("state-gap")["files"][0]
    check("gap-only: gap is nonzero", f6["gap"] > 0, info="gap {}".format(f6["gap"]))
    check("gap-only: not drifted", f6["drifted"] is False,
          detail="a landing gap alone must not also read as drift")

    # state: drift-only - no net size change predicted or observed, but content differs
    t7 = os.path.join(d, "g-drift-only.md")
    _write(t7, "x" * 100)
    ledger.open_run([t7], run_id="state-drift", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("state-drift", {"delta": 0, "bucket": "global", "gated": True, "target": t7})
    _write(t7, "y" * 100)          # same size, different content
    f7 = close.close("state-drift")["files"][0]
    check("drift-only: gap is zero", f7["gap"] == 0, info="gap {}".format(f7["gap"]))
    check("drift-only: drifted is true", f7["drifted"] is True)

    # state: both - the edit did not land at all, AND something else touched the file
    t8 = os.path.join(d, "h-both.md")
    _write(t8, "x" * 1000)
    ledger.open_run([t8], run_id="state-both", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("state-both", {"delta": -1840, "bucket": "global", "gated": True, "target": t8})
    _write(t8, "y" * 1000)         # our edit never landed (same size) AND content changed
    r8 = close.close("state-both")
    f8 = r8["files"][0]
    check("both: gap is nonzero", f8["gap"] > 0, info="gap {}".format(f8["gap"]))
    check("both: drifted is also true", f8["drifted"] is True,
          detail="a half-landed edit plus outside interference must show both, not just one")
    check("both: two distinct findings are reported", len(r8["findings"]) == 2,
          info="{}".format(len(r8["findings"])),
          detail="the landing gap and the drift are different problems with different fixes")

    print("\ncase: a multi-target run reconciles every target, not just the first")
    m1 = os.path.join(d, "multi-1.md")
    m2 = os.path.join(d, "multi-2.md")
    m3 = os.path.join(d, "multi-3.md")
    _write(m1, "x" * 500)
    _write(m2, "x" * 500)
    _write(m3, "x" * 500)
    ledger.open_run([m1, m2, m3], run_id="multi", now="2026-08-04T00:00:00Z")
    ledger.add_proposal("multi", {"delta": -100, "bucket": "project", "gated": False, "target": m1})
    ledger.add_proposal("multi", {"delta": -100, "bucket": "project", "gated": False, "target": m2})
    ledger.add_proposal("multi", {"delta": -100, "bucket": "project", "gated": False, "target": m3})
    _write(m1, "x" * 400)          # landed exactly
    _write(m2, "x" * 400)          # landed exactly
    _write(m3, "x" * 480)          # only -20, not -100 - the later target is the mismatch
    rm = close.close("multi")
    check("multi-target: three files are reported", len(rm["files"]) == 3,
          info="{}".format(len(rm["files"])))
    check("multi-target: the mismatched later target fails reconciliation", rm["reconciled"] is False,
          detail="a check that only looks at the first target would pass this")
    check("multi-target: the mismatch names the third file, not the first",
          bool(rm["findings"]) and m3 in rm["findings"][0],
          info=rm["findings"][0] if rm["findings"] else "",
          detail="findings was empty, nothing to index")

report("core-close")
