"""Argument parsing and the three output channels.

stdout is JSON and nothing else, so a caller can json.loads it
unconditionally. Everything human goes to stderr. The exit code carries the
verdict: 0 clean, 1 gate refused (or reconcile failed), 2 usage or internal
error. A crash must never read as a refusal (1) and a refusal must never
read as clean (0) - conflating either is the exact silent-failure class this
core exists to remove, so the mapping below is deliberately narrow.
"""

import argparse
import json
import sys

from . import close as close_mod
from . import gate as gate_mod
from . import ledger, measure, price, route

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_ERROR = 2


def _emit(payload):
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _parser():
    p = argparse.ArgumentParser(prog="notation-core", add_help=True)
    sub = p.add_subparsers(dest="cmd")

    m = sub.add_parser("measure")
    m.add_argument("path")

    o = sub.add_parser("open")
    # --target is repeatable and every file the run will touch belongs here:
    # close() reconciles registered targets and nothing else, so an
    # unregistered file is one whose failed write reports as success.
    o.add_argument("--target", action="append", required=True)
    o.add_argument("--run-id", required=True)
    o.add_argument("--now", required=True)

    reg = sub.add_parser("register")
    reg.add_argument("--run-id", required=True)
    reg.add_argument("--target", action="append", required=True)

    r = sub.add_parser("route")
    r.add_argument("--text-file", required=True)
    r.add_argument("--target", required=True)
    r.add_argument("--notes-dir", default="~/.claude/notes")

    pr = sub.add_parser("price")
    # --removed is OPTIONAL: a pure addition removes nothing, and price()
    # treats removed_path=None as exactly that (0 removed chars) - a
    # legitimate case, not a missing argument. Omitting the flag is how a
    # caller says "nothing removed"; passing an empty string or a path that
    # does not exist means a path WAS intended and is wrong, and both must
    # keep refusing (see price.py) so the two cases are never conflated.
    pr.add_argument("--removed", default=None)
    pr.add_argument("--added", required=True)
    pr.add_argument("--target", required=True)

    rec = sub.add_parser("price-record")
    rec.add_argument("--run-id", required=True)
    rec.add_argument("--delta", type=int, required=True)
    rec.add_argument("--bucket", required=True)
    rec.add_argument("--target", required=True)

    g = sub.add_parser("gate")
    g.add_argument("--run-id", required=True)
    # Optional: gate() cannot know a target's scope when it cannot load the
    # ledger that names the targets (that is exactly why it raises rather
    # than guessing - see gate.py and ledger.py). The CLI is the one place
    # that is ever told which file this run is about to write, so the CLI
    # is where the fail-open/fail-closed split below has to live. Omitted
    # is treated the same as global: silence must never read as a pass on
    # the global side.
    g.add_argument("--target", default=None)

    c = sub.add_parser("close")
    c.add_argument("--run-id", required=True)
    return p


def _gate_load_failure(run_id, target, exc):
    """-> exit code for a gate whose ledger could not be loaded.

    gate() raises RunLedgerError rather than guess a verdict, because
    without the ledger it does not know the target's scope. This function
    is where that scope becomes known (from the --target the caller
    supplied) and where the asymmetry the gate exists to enforce is
    applied one level up:

    - global (or unspecified) target: BLOCK the write. The gate protects
      the file every session pays for, so a missing verdict there must
      never read as a pass.
    - project target: PERMIT the write. The project tier is meant to stay
      flexible, so a missing verdict there is a warning, not a stop.

    Either way the failure is explained on stderr; stdout only carries
    JSON on the permit path, since that path exits 0 and a 0 exit is a
    caller's signal to expect parseable JSON.
    """
    bucket = measure.resolve_bucket(target) if target else "global"
    reason = "gate could not load run '{}': {}: {}".format(
        run_id, type(exc).__name__, exc
    )
    if bucket == "project":
        sys.stderr.write(reason + "\n")
        sys.stderr.write(
            "target '{}' is project-scoped; permitting the write without "
            "a verdict (fail-open)\n".format(target)
        )
        _emit({
            "run_id": run_id,
            "refused": False,
            "permitted_without_verdict": True,
            "bucket": bucket,
            "reasons": [reason],
        })
        return EXIT_OK

    sys.stderr.write(reason + "\n")
    sys.stderr.write(
        "target '{}' is global or unspecified; blocking the write "
        "(fail-closed)\n".format(target)
    )
    return EXIT_ERROR


def main(argv):
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return EXIT_ERROR
    if not args.cmd:
        sys.stderr.write("no subcommand given\n")
        return EXIT_ERROR

    try:
        if args.cmd == "measure":
            _emit(measure.measure(args.path))
            return EXIT_OK

        if args.cmd == "open":
            _emit(ledger.open_run(args.target, args.run_id, args.now))
            return EXIT_OK

        if args.cmd == "register":
            _emit({
                "run_id": args.run_id,
                "registered": [ledger.register_target(args.run_id, t)
                               for t in args.target],
            })
            return EXIT_OK

        if args.cmd == "route":
            text = measure.read_text(args.text_file)
            verdict = route.route(text, args.target, args.notes_dir)
            _emit(verdict)
            # An unreadable note is counted in notes_searched but can never
            # match, so it has to be said out loud or it reads as a miss.
            for item in verdict["unreadable"]:
                sys.stderr.write(
                    "note could not be read, so it was ranked on its filename "
                    "alone and cannot match on content: {} ({})\n".format(
                        item["path"], item["error"]
                    )
                )
            return EXIT_OK

        if args.cmd == "price":
            _emit(price.price(args.removed, args.added, args.target))
            return EXIT_OK

        if args.cmd == "price-record":
            bucket = args.bucket
            ledger.add_proposal(args.run_id, {
                "delta": args.delta, "bucket": bucket,
                "gated": measure.is_gated(bucket), "target": args.target,
            })
            _emit({"recorded": True, "run_id": args.run_id})
            return EXIT_OK

        if args.cmd == "gate":
            try:
                verdict = gate_mod.gate(args.run_id)
            except ledger.RunLedgerError as exc:
                return _gate_load_failure(args.run_id, args.target, exc)
            _emit(verdict)
            for reason in verdict["reasons"]:
                sys.stderr.write(reason + "\n")
            return EXIT_REFUSED if verdict["refused"] else EXIT_OK

        if args.cmd == "close":
            report = close_mod.close(args.run_id)
            _emit(report)
            for finding in report["findings"]:
                sys.stderr.write(finding + "\n")
            # Not a finding (it is the ordinary outcome for a file the run
            # wrote to), but it must never pass for a clean bill of health.
            for path in report["drift_undetermined"]:
                sys.stderr.write(
                    "{}: outside edits could NOT be ruled out - a size and a "
                    "pre-run hash cannot separate this run's own write from "
                    "someone else's\n".format(path)
                )
            return EXIT_OK if report["reconciled"] else EXIT_REFUSED

    except Exception as exc:                       # noqa: BLE001 - intentional
        sys.stderr.write("{}: {}\n".format(type(exc).__name__, exc))
        return EXIT_ERROR

    sys.stderr.write("unhandled subcommand: {}\n".format(args.cmd))
    return EXIT_ERROR
