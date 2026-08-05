#!/usr/bin/env python3
"""Run ledger: identity, pre-run hashes, and refusing foreign runs."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import ledger

with tempfile.TemporaryDirectory() as d:
    os.environ["NOTATION_RUNS_DIR"] = os.path.join(d, "runs")
    target = os.path.join(d, "CLAUDE.md")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("original\n")

    print("\ncase: open records a pre-run hash per target")
    run = ledger.open_run([target], run_id="test-run-1", now="2026-08-04T00:00:00Z")
    check("run id is recorded", run["run_id"] == "test-run-1")
    check("target is recorded", target in run["targets"])
    check("with a hash", len(run["targets"][target]["sha256"]) == 64)
    check("and a pre-run size", run["targets"][target]["chars"] == 9)
    check("no proposals yet", run["proposals"] == [])

    print("\ncase: proposals accumulate")
    ledger.add_proposal("test-run-1", {"delta": -500, "bucket": "global"})
    ledger.add_proposal("test-run-1", {"delta": 120, "bucket": "global"})
    reloaded = ledger.load("test-run-1")
    check("both proposals are on the ledger", len(reloaded["proposals"]) == 2)
    check("in order", reloaded["proposals"][0]["delta"] == -500)

    print("\ncase: a foreign run id is refused, not repaired")
    raised = False
    try:
        ledger.load("never-opened")
    except LookupError:
        raised = True
    check("loading an unknown run raises LookupError", raised, detail="it must never guess")

    print("\ncase: hashing detects outside edits")
    before = ledger.file_hash(target)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write("someone else wrote this\n")
    check("the hash changes when the file changes", ledger.file_hash(target) != before)

report("core-ledger")
