#!/usr/bin/env python3
"""open -> route -> price -> gate -> apply -> close, end to end.

The unit tests each prove one subcommand. This proves the sequence composes:
a relocation that is drafted, priced, gated, applied, and then reconciles.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import check, report

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY = os.path.join(REPO, "scripts", "notation-core.py")


def run(args, env):
    e = dict(os.environ)
    e.update(env)
    p = subprocess.Popen([sys.executable, ENTRY] + args,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    out, err = p.communicate()
    return p.returncode, out.decode("utf-8"), err.decode("utf-8")


with tempfile.TemporaryDirectory() as d:
    env = {"NOTATION_RUNS_DIR": os.path.join(d, "runs")}
    notes = os.path.join(d, "notes")
    os.makedirs(notes)
    with open(os.path.join(notes, "railway.md"), "w", encoding="utf-8") as fh:
        fh.write("# Railway\n\n## Auth\nToken auth notes.\n")

    claude = os.path.join(d, "CLAUDE.md")
    body = "### Railway\n" + ("Railway bucket TTL detail. " * 40) + "\n"
    with open(claude, "w", encoding="utf-8") as fh:
        fh.write("# CLAUDE.md\n\n" + body)
    before = os.path.getsize(claude)

    proposal = os.path.join(d, "proposal.txt")
    with open(proposal, "w", encoding="utf-8") as fh:
        fh.write(body)
    pointer = os.path.join(d, "pointer.txt")
    with open(pointer, "w", encoding="utf-8") as fh:
        fh.write("### Railway\nBucket TTL at create time. Detail: `notes/railway.md`\n")

    print("\ncase: a body-sized proposal must become a note")
    rc, out, _ = run(["route", "--text-file", proposal, "--target", claude,
                      "--notes-dir", notes], env)
    r = json.loads(out)
    check("band is must_note", r["band"] == "must_note", info=r["band"])
    check("railway.md is offered as a candidate",
          any("railway.md" in c["path"] for c in r["candidates"]),
          detail="candidates were {}".format([c["path"] for c in r["candidates"]]))
    check("and it says how many notes it searched", r["notes_searched"] == 1)

    print("\ncase: the sequence gates, applies, and reconciles")
    run(["open", "--target", claude, "--run-id", "rt", "--now", "2026-08-04T00:00:00Z"], env)
    _, out_p, _ = run(["price", "--removed", proposal, "--added", pointer,
                       "--target", claude], env)
    delta = json.loads(out_p)["delta"]
    check("the relocation prices negative", delta < 0, info="{}".format(delta))

    run(["price-record", "--run-id", "rt", "--delta", str(delta),
         "--bucket", "global", "--target", claude], env)
    rc_g, _, _ = run(["gate", "--run-id", "rt"], env)
    check("the gate passes a net reduction", rc_g == 0, info="rc={}".format(rc_g))

    with open(claude, "w", encoding="utf-8") as fh:
        fh.write("# CLAUDE.md\n\n" + open(pointer, encoding="utf-8").read())
    after = os.path.getsize(claude)
    check("the file really shrank", after < before, info="{} -> {}".format(before, after))

    rc_c, out_c, err_c = run(["close", "--run-id", "rt"], env)
    check("close reconciles to zero gap", json.loads(out_c)["files"][0]["gap"] == 0,
          detail="stderr: {}".format(err_c.strip()))
    check("and exits 0", rc_c == 0, info="rc={}".format(rc_c))

    print("\ncase: applying a DIFFERENT edit than the one priced must not reconcile")
    run(["open", "--target", claude, "--run-id", "rt-wrong",
         "--now", "2026-08-04T00:00:00Z"], env)
    _, out_p2, _ = run(["price", "--removed", proposal, "--added", pointer,
                        "--target", claude], env)
    delta2 = json.loads(out_p2)["delta"]
    run(["price-record", "--run-id", "rt-wrong", "--delta", str(delta2),
         "--bucket", "global", "--target", claude], env)
    rc_g2, _, _ = run(["gate", "--run-id", "rt-wrong"], env)
    check("the gate still passes the same predicted delta", rc_g2 == 0,
          info="rc={}".format(rc_g2))

    # Apply an edit that does NOT match what was priced: append instead of
    # replacing, so the observed shrink never happens.
    with open(claude, "a", encoding="utf-8") as fh:
        fh.write("\nan unrelated extra line that was never priced\n")

    rc_c2, out_c2, err_c2 = run(["close", "--run-id", "rt-wrong"], env)
    report2 = json.loads(out_c2)
    check("close reports a nonzero gap for the mismatched edit",
          report2["files"][0]["gap"] != 0,
          detail="stderr: {}".format(err_c2.strip()))
    check("and does not exit 0", rc_c2 != 0, info="rc={}".format(rc_c2))

report("core-roundtrip")
