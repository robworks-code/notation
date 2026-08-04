#!/usr/bin/env python3
"""Ledger error handling: three distinct failure modes are distinguishable."""

import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import ledger

with tempfile.TemporaryDirectory() as d:
    os.environ["NOTATION_RUNS_DIR"] = os.path.join(d, "runs")
    runs_d = os.path.join(d, "runs")
    os.makedirs(runs_d, exist_ok=True)

    print("\nfailure mode 1: run never opened (file not found)")
    caught = None
    try:
        ledger.load("never-opened")
    except Exception as e:
        caught = type(e).__name__
    check("raises LookupError", caught == "LookupError", detail=f"got {caught}")

    try:
        ledger.load("never-opened")
    except LookupError as e:
        check("message names the run id", "never-opened" in str(e))

    print("\nfailure mode 2: file contains invalid JSON")
    bad_json_path = os.path.join(runs_d, "bad-json.json")
    with open(bad_json_path, "w", encoding="utf-8") as fh:
        fh.write("{ not valid json")

    caught = None
    try:
        ledger.load("bad-json")
    except Exception as e:
        caught = type(e).__name__
    check("raises RunLedgerJSONError", caught == "RunLedgerJSONError", detail=f"got {caught}")

    try:
        ledger.load("bad-json")
    except ledger.RunLedgerJSONError as e:
        check("message names the run id", "bad-json" in str(e))
        check("message describes JSON error", "JSON" in str(e))

    print("\nfailure mode 3: valid JSON but invalid ledger structure")
    bad_struct_path = os.path.join(runs_d, "bad-struct.json")
    with open(bad_struct_path, "w", encoding="utf-8") as fh:
        json.dump({"foo": "bar"}, fh)

    caught = None
    try:
        ledger.load("bad-struct")
    except Exception as e:
        caught = type(e).__name__
    check("raises RunLedgerInvalidError", caught == "RunLedgerInvalidError", detail=f"got {caught}")

    try:
        ledger.load("bad-struct")
    except ledger.RunLedgerInvalidError as e:
        check("message names the run id", "bad-struct" in str(e))
        check("message names missing keys", "missing keys" in str(e) or "invalid" in str(e).lower())

    print("\nfailure mode 3b: add_proposal validates ledger structure")
    try:
        ledger.add_proposal("bad-struct", {"delta": 100, "bucket": "global"})
        check("add_proposal raises on invalid ledger", False, detail="should have raised")
    except ledger.RunLedgerInvalidError:
        check("add_proposal raises RunLedgerInvalidError", True)

    print("\ndistinguishability: the three are catchable and distinct")
    check("LookupError is not a RunLedgerError",
          not issubclass(LookupError, ledger.RunLedgerError))
    check("RunLedgerJSONError is a RunLedgerError",
          issubclass(ledger.RunLedgerJSONError, ledger.RunLedgerError))
    check("RunLedgerInvalidError is a RunLedgerError",
          issubclass(ledger.RunLedgerInvalidError, ledger.RunLedgerError))
    check("RunLedgerJSONError is not RunLedgerInvalidError",
          ledger.RunLedgerJSONError != ledger.RunLedgerInvalidError)

report("core-ledger-errors")
