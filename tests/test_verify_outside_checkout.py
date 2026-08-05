#!/usr/bin/env python3
"""verify.sh must refuse, not fail, when it is not in a git checkout.

scripts/verify.sh and tests/ ship inside the plugin tarball, so they land in
~/.claude/plugins/cache/.../notation/<version>/. Every scan in the gate
enumerates the shipped files with `git ls-files`, which returns nothing there.
The scans notice the empty list and fail loudly - that is the false-zero rule
working, and it is not what this test is about. The problem was the verdict
word: a gate that COULD NOT RUN printed `VERIFY FAILED`, which to the only
person who ever sees it reads as "this plugin is broken".

The opposite mutation - a guard that fires even inside a checkout - needs no
test here. It would exit 2 on the repo's own gate and turn every CI job red on
the first push, which is a louder signal than any assertion in this file.
"""

import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import check, report  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tarball_copy(dest):
    """Copy the tracked tree WITHOUT .git, the way the plugin ships."""
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True
    ).stdout.split()
    for rel in tracked:
        src = os.path.join(REPO, rel)
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    return tracked


def main():
    tmp = tempfile.mkdtemp(prefix="notation-tarball-")
    try:
        tracked = tarball_copy(tmp)

        # Without this the whole file could pass having copied nothing into an
        # empty directory, where a missing verify.sh would also "not print
        # VERIFY FAILED".
        check(
            "the copy actually contains the shipped gate",
            len(tracked) >= 20 and os.path.exists(os.path.join(tmp, "scripts/verify.sh")),
            info="copied {} tracked file(s)".format(len(tracked)),
        )
        check(
            "the copy is not a git checkout",
            not os.path.exists(os.path.join(tmp, ".git")),
        )

        # A temp dir under a git checkout would inherit ITS work tree and make
        # the guard a no-op, so confirm the copy really has no work tree above
        # it before believing anything the run reports.
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=tmp, capture_output=True, text=True,
        )
        check(
            "no parent work tree reaches the copy",
            inside.returncode != 0,
            detail="git claims a work tree at {} - the guard cannot be tested here".format(tmp),
        )
        if inside.returncode == 0:
            return report("verify-outside-checkout")

        run = subprocess.run(
            ["sh", os.path.join(tmp, "scripts/verify.sh")],
            cwd=tmp, capture_output=True, text=True,
        )
        out = run.stdout + run.stderr

        check(
            "exits 2 (no verdict), not 1 (real failures) or 0 (clean)",
            run.returncode == 2,
            detail="exit {}".format(run.returncode),
        )
        check(
            "never prints VERIFY FAILED for a gate that could not run",
            "VERIFY FAILED" not in out,
        )
        check(
            "never prints VERIFY PASSED either",
            "VERIFY PASSED" not in out,
        )
        check(
            "says it could not verify, and why",
            "CANNOT VERIFY" in out and "git ls-files" in out,
            detail="output was: {!r}".format(out[:300]),
        )
        check(
            "points at the repo, since the reader is holding an install",
            "github.com/robworks-code/notation" in out,
        )
        check(
            "stops before running any scan, so no scan reports a false zero",
            "scanned 0 tracked file(s)" not in out,
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return report("verify-outside-checkout")


if __name__ == "__main__":
    main()
