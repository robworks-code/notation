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
    check("raises RunLedgerMissingError", caught == "RunLedgerMissingError", detail=f"got {caught}")

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
    check("RunLedgerMissingError is a RunLedgerError",
          issubclass(ledger.RunLedgerMissingError, ledger.RunLedgerError))
    check("RunLedgerMissingError is a LookupError (backward compat)",
          issubclass(ledger.RunLedgerMissingError, LookupError))
    check("RunLedgerJSONError is a RunLedgerError",
          issubclass(ledger.RunLedgerJSONError, ledger.RunLedgerError))
    check("RunLedgerInvalidError is a RunLedgerError",
          issubclass(ledger.RunLedgerInvalidError, ledger.RunLedgerError))
    check("All three are distinct from each other",
          len({ledger.RunLedgerMissingError, ledger.RunLedgerJSONError, ledger.RunLedgerInvalidError}) == 3)

    print("\nunified catchability: all three can be caught as RunLedgerError")
    missing_caught = False
    try:
        ledger.load("never-opened")
    except ledger.RunLedgerError:
        missing_caught = True
    check("never-opened caught as RunLedgerError", missing_caught)

    json_caught = False
    try:
        ledger.load("bad-json")
    except ledger.RunLedgerError:
        json_caught = True
    check("invalid JSON caught as RunLedgerError", json_caught)

    struct_caught = False
    try:
        ledger.load("bad-struct")
    except ledger.RunLedgerError:
        struct_caught = True
    check("invalid structure caught as RunLedgerError", struct_caught)

report("core-ledger-errors")
