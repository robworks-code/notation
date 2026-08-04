#!/usr/bin/env python3
"""Channel separation and exit codes.

Conflating 'the gate refused' (1) with 'the script crashed' (2) is the failure
mode this whole effort exists to remove, so they are asserted separately.

Also covers the fail-open/fail-closed asymmetry adjudicated during Task 5's
review: gate() itself raises rather than guess a verdict when it cannot load
a ledger, because without the ledger it does not know the target's scope.
The CLI is the one place that IS told the target, so the CLI is where that
asymmetry has to resolve - a missing verdict blocks a global write and
permits a project write, with an explicit warning either way.
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


def run(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.Popen([sys.executable, ENTRY] + args,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    out, err = p.communicate()
    return p.returncode, out.decode("utf-8"), err.decode("utf-8")


with tempfile.TemporaryDirectory() as d:
    runs = os.path.join(d, "runs")
    target = os.path.join(d, "CLAUDE.md")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("# T\n\nbody\n")
    env = {"NOTATION_RUNS_DIR": runs}

    print("\ncase: stdout is JSON only")
    rc, out, err = run(["measure", target], env)
    check("exit 0 on a clean call", rc == 0, info="rc={}".format(rc))
    parsed = None
    try:
        parsed = json.loads(out)
    except ValueError:
        pass
    check("stdout parses as JSON with no preamble", parsed is not None,
          detail="stdout was: {!r}".format(out[:120]))
    # "# T\n\nbody\n" is 10 chars, not 13 - the brief's own check asserted 13
    # for this fixture, which does not match; corrected against the actual
    # measured value rather than reproduced wrong.
    check("and carries the measurement", parsed and parsed["chars"] == 10)

    print("\ncase: exit 2 is usage or internal error, never 1")
    rc_bad, _, err_bad = run(["nosuchcommand"], env)
    check("an unknown subcommand exits 2", rc_bad == 2, info="rc={}".format(rc_bad))
    check("and explains on stderr", bool(err_bad.strip()))

    rc_missing, _, _ = run(["close", "--run-id", "never-opened"], env)
    check("an unknown run id exits 2, not 1", rc_missing == 2,
          detail="a missing ledger is an error, not a gate refusal")

    print("\ncase: exit 1 is reserved for a refusal")
    run(["open", "--target", target, "--run-id", "r1", "--now", "2026-08-04T00:00:00Z"], env)
    run(["price-record", "--run-id", "r1", "--delta", "500",
         "--bucket", "global", "--target", target], env)
    rc_gate, out_gate, _ = run(["gate", "--run-id", "r1"], env)
    check("a refused gate exits 1", rc_gate == 1, info="rc={}".format(rc_gate))
    check("and still emits JSON", json.loads(out_gate)["refused"] is True)

    print("\ncase: a clean gate exits 0")
    run(["open", "--target", target, "--run-id", "r2", "--now", "2026-08-04T00:00:00Z"], env)
    run(["price-record", "--run-id", "r2", "--delta", "-500",
         "--bucket", "global", "--target", target], env)
    rc_ok, _, _ = run(["gate", "--run-id", "r2"], env)
    check("a passing gate exits 0", rc_ok == 0, info="rc={}".format(rc_ok))

    print("\ncase: every subcommand's success path emits parseable JSON, not just measure")

    rc_open, out_open, _ = run(
        ["open", "--target", target, "--run-id", "r3", "--now", "2026-08-04T00:00:00Z"], env)
    check("open exits 0", rc_open == 0, info="rc={}".format(rc_open))
    try:
        json.loads(out_open)
        open_ok = True
    except ValueError:
        open_ok = False
    check("open stdout parses as JSON", open_ok, detail=repr(out_open[:120]))

    notes_dir = os.path.join(d, "notes")
    os.makedirs(notes_dir)
    text_file = os.path.join(d, "proposed.txt")
    with open(text_file, "w", encoding="utf-8") as fh:
        fh.write("a short proposed addition")
    rc_route, out_route, _ = run(
        ["route", "--text-file", text_file, "--target", target, "--notes-dir", notes_dir], env)
    check("route exits 0", rc_route == 0, info="rc={}".format(rc_route))
    try:
        json.loads(out_route)
        route_ok = True
    except ValueError:
        route_ok = False
    check("route stdout parses as JSON", route_ok, detail=repr(out_route[:120]))

    removed_file = os.path.join(d, "removed.txt")
    added_file = os.path.join(d, "added.txt")
    with open(removed_file, "w", encoding="utf-8") as fh:
        fh.write("old text")
    with open(added_file, "w", encoding="utf-8") as fh:
        fh.write("new text, a bit longer")
    rc_price, out_price, _ = run(
        ["price", "--removed", removed_file, "--added", added_file, "--target", target], env)
    check("price exits 0", rc_price == 0, info="rc={}".format(rc_price))
    try:
        json.loads(out_price)
        price_ok = True
    except ValueError:
        price_ok = False
    check("price stdout parses as JSON", price_ok, detail=repr(out_price[:120]))

    # delta 0 so close's reconciliation matches: the target file is never
    # actually rewritten in this test, so the true post-run delta is 0 too.
    rc_rec, out_rec, _ = run(
        ["price-record", "--run-id", "r3", "--delta", "0", "--bucket", "project",
         "--target", target], env)
    check("price-record exits 0", rc_rec == 0, info="rc={}".format(rc_rec))
    try:
        json.loads(out_rec)
        rec_ok = True
    except ValueError:
        rec_ok = False
    check("price-record stdout parses as JSON", rec_ok, detail=repr(out_rec[:120]))

    rc_close, out_close, _ = run(["close", "--run-id", "r3"], env)
    check("close exits 0 when reconciled", rc_close == 0, info="rc={}".format(rc_close))
    try:
        json.loads(out_close)
        close_ok = True
    except ValueError:
        close_ok = False
    check("close stdout parses as JSON", close_ok, detail=repr(out_close[:120]))

    print("\ncase: fail-closed / fail-open when the gate has no ledger to load")

    # A global target lives at exactly ~/.claude/CLAUDE.md, so the asymmetry
    # test needs its own HOME - the repo's real home directory must never be
    # touched by a test.
    with tempfile.TemporaryDirectory() as home:
        claude_dir = os.path.join(home, ".claude")
        os.makedirs(claude_dir)
        global_target = os.path.join(claude_dir, "CLAUDE.md")
        with open(global_target, "w", encoding="utf-8") as fh:
            fh.write("# global\n")
        asym_env = {"NOTATION_RUNS_DIR": runs, "HOME": home}

        rc_g, out_g, err_g = run(
            ["gate", "--run-id", "never-opened-global", "--target", global_target], asym_env)
        check("a global target with no ledger blocks (exit non-zero, not 0 or 1)",
              rc_g not in (0, 1), info="rc={}".format(rc_g))
        check("and explains the block on stderr", "blocking" in err_g,
              detail=repr(err_g[:200]))
        check("stdout stays empty on the blocked path", out_g == "",
              detail=repr(out_g[:120]))

        rc_none, _, err_none = run(
            ["gate", "--run-id", "never-opened-no-target"], asym_env)
        check("an unspecified target also blocks (treated as global)",
              rc_none not in (0, 1), info="rc={}".format(rc_none))
        check("and says so on stderr", "blocking" in err_none,
              detail=repr(err_none[:200]))

        rc_p, out_p, err_p = run(
            ["gate", "--run-id", "never-opened-project", "--target", target], asym_env)
        check("a project target with no ledger permits (exit 0)", rc_p == 0,
              info="rc={}".format(rc_p))
        check("and warns on stderr", "fail-open" in err_p, detail=repr(err_p[:200]))
        try:
            parsed_p = json.loads(out_p)
        except ValueError:
            parsed_p = None
        check("and still emits parseable JSON on stdout", parsed_p is not None,
              detail=repr(out_p[:200]))
        check("marked as a permit without a verdict",
              parsed_p and parsed_p["permitted_without_verdict"] is True
              and parsed_p["refused"] is False)

report("core-cli")
