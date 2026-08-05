#!/usr/bin/env python3
"""Tests for check 7's backup listing recipe.

Check 7 sorts backups into families and treats them differently, so a family the
listing does not surface is a family nothing ever prunes - which is exactly how
issues #14 and #20 arose. Prose can claim to cover five families while the
commands find three; only running them proves otherwise.

So: extract the shipped ```bash block, run it against a synthetic HOME holding
one planted file per family, and require every plant to appear in the output.

Run: python3 tests/test_backup_lifecycle.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKLIST = os.path.join(
    REPO, "skills", "notation-audit", "references", "audit-checklist.md"
)

failures = []


def check(name, condition, detail="", info=""):
    """Print one row. `detail` is FAILURE-only; `info` prints either way."""
    status = "ok  " if condition else "FAIL"
    suffix = info if condition else " - ".join(x for x in (info, detail) if x)
    print(f"  [{status}] {name}" + (f" - {suffix}" if suffix else ""))
    if not condition:
        failures.append(name)


def block_under(heading):
    """The first ```bash block following a given check-7 heading."""
    text = open(CHECKLIST, encoding="utf-8").read()
    section = text.split(heading, 1)
    if len(section) != 2:
        return None
    m = re.search(r"```bash\n(.*?)\n```", section[1], re.DOTALL)
    return m.group(1) if m else None


# Every runnable block in check 7, not just the listing one. A block with no
# coverage is where the nomatch-noise defect hid the first time: the listing
# block was rewritten to stay silent while the probe beside it still errored on
# the healthy path.
CHECK7_BLOCKS = [
    "### List every family",
    "### Which run backups are safe to remove",
    "### Defer to an existing rotation policy",
]


def listing_block():
    return block_under("### List every family")


def plant(home, project):
    """One backup per family check 7 claims to list. Returns {family: path}."""
    enc = project.replace("/", "-").replace(".", "-")
    paths = {
        # 1 config snapshot - listed, but never proposed for deletion.
        "config snapshot": f"{home}/.claude/CLAUDE.md.bak.20260730-141530",
        # 2 the user's own note backup - notation must never write here.
        "user note backup": f"{home}/.claude/notes/gcloud.md.bak.20260730-141530",
        # 3 run dirs, both scopes. Listed as directories, one per run.
        "project run dir": f"{home}/.claude/notation-backups/{enc}/20260730-141530/CLAUDE.md",
        "global run dir": f"{home}/.claude/notation-backups/global/20260730-141530/CLAUDE.md",
        # 5 in-repo backup - a defect, and only findable from the project dir.
        # Kept relative: `find .` reports a relative path, which is correct and
        # is what a real run shows.
        "in-repo backup": "./CLAUDE.md.bak.20260730-141530",
    }
    for p in paths.values():
        full = p if os.path.isabs(p) else os.path.join(project, p)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write("backup\n")
    # 4 another project's backup dir - must be COUNTED, never listed per-file,
    # so it is planted but deliberately not required in the output.
    other = f"{home}/.claude/notation-backups/-Users-x-git-other/20260101-000000"
    os.makedirs(other, exist_ok=True)
    open(f"{other}/CLAUDE.md", "w").write("other\n")
    return paths, other


ZSH = "/bin/zsh"


def main():
    block = listing_block()
    check("check 7 ships one bash listing block", block is not None)
    if block is None:
        return 1

    # A missing zsh must fail loudly and by name. Left to itself this surfaces as
    # a bare FileNotFoundError traceback from subprocess, which reads as a broken
    # test rather than a missing dependency - and the recipe under test exists
    # specifically to survive zsh's nomatch abort, so no other shell can stand in.
    check(
        "a real zsh is available to run the shipped recipe",
        os.path.exists(ZSH),
        detail="{} not found - install zsh; sh and bash cannot prove this recipe".format(ZSH),
    )
    if not os.path.exists(ZSH):
        return 1

    tmp = tempfile.mkdtemp(prefix="notation-bak-")
    try:
        # A dotted path, so the encoding's dot handling is exercised here too -
        # a project dir this rule mishandles silently lists nothing.
        home = os.path.join(tmp, "home")
        project = os.path.join(tmp, "home", "git", "my.app")
        os.makedirs(project, exist_ok=True)
        paths, other = plant(home, project)

        # zsh, not sh: the shipped recipe runs in the Bash tool, whose shell is
        # zsh, and the nomatch abort this recipe exists to avoid is zsh-only.
        #
        # PWD must be set explicitly. `subprocess(cwd=...)` changes the real
        # working directory but leaves the inherited PWD env var pointing at the
        # parent's - and the encoding reads $PWD, so without this the recipe
        # resolves THIS repo's backup dir instead of the fixture's and every
        # plant appears missing. A real shell sets PWD on cd; the fixture must
        # match that, not accidentally test a stale-PWD scenario.
        env = dict(os.environ, HOME=home, PWD=project)
        out = subprocess.run(
            [ZSH, "-c", block],
            capture_output=True,
            text=True,
            cwd=project,
            env=env,
        )

        for family, path in paths.items():
            # Run backups are listed one directory per run; user backups are
            # listed per file. Assert on whichever unit the recipe reports.
            want = os.path.dirname(path) if "run dir" in family else path
            check(
                f"listing surfaces the {family}",
                want in out.stdout,
                f"{want} absent from the recipe's output",
            )

        check(
            "the other-projects count excludes this project and global/",
            "other projects with backups: 1" in out.stdout,
            "the count must exclude this project and global/, or it "
            "double-counts family 3 and reports 'other projects' on a machine "
            "that has only this one. Only -Users-x-git-other is foreign here, "
            f"so the count must be 1; stdout: {out.stdout.strip()!r}",
        )
        check(
            "another project's backups are counted, not enumerated per-file",
            other not in out.stdout,
            "a per-file path from another project leaked into the listing - "
            "the audit must never act on backups whose run it cannot verify",
        )
        # The healthy path is "no backups at all", so a recipe that errors on an
        # empty match trains the reader to ignore its own output.
        check(
            "the recipe is silent on stderr when everything matches",
            out.stderr.strip() == "",
            f"stderr: {out.stderr.strip()!r}",
        )

        # Same recipe, nothing planted: still must not error.
        empty = os.path.join(tmp, "empty")
        os.makedirs(os.path.join(empty, "proj"), exist_ok=True)
        bare = subprocess.run(
            [ZSH, "-c", block],
            capture_output=True,
            text=True,
            cwd=os.path.join(empty, "proj"),
            env=dict(os.environ, HOME=empty, PWD=os.path.join(empty, "proj")),
        )
        check(
            "the recipe is silent when NO backups exist (the normal state)",
            bare.stderr.strip() == "" and "no matches found" not in bare.stderr,
            f"stderr: {bare.stderr.strip()!r}",
        )
        # Finding 1 from review: the listing block was made silent while the
        # rotation-policy probe beside it still errored on the healthy path
        # (grep exits 1 with no match, 2 with no file; ls exits 1 when absent).
        # Every runnable block in the check gets the same treatment.
        for heading in CHECK7_BLOCKS:
            blk = block_under(heading)
            check(f"block exists: {heading}", blk is not None)
            if blk is None:
                continue
            r = subprocess.run(
                [ZSH, "-c", blk],
                capture_output=True, text=True,
                cwd=os.path.join(empty, "proj"),
                env=dict(os.environ, HOME=empty, PWD=os.path.join(empty, "proj")),
            )
            check(
                f"silent on the healthy path: {heading}",
                r.stderr.strip() == "",
                f"stderr: {r.stderr.strip()!r}",
            )

        # The .verified marker is the only signal distinguishing a spent backup
        # from the sole surviving copy of a run that failed. Age must never
        # stand in for it, so the sorter must key on the marker alone - here the
        # UNVERIFIED dir is the older one, which an age heuristic would delete.
        sorter = block_under("### Which run backups are safe to remove")
        check("check 7 ships a marker-sorting block", sorter is not None)
        if sorter is not None:
            h2 = os.path.join(tmp, "mark")
            spent = f"{h2}/.claude/notation-backups/global/20260730-141530"
            keep = f"{h2}/.claude/notation-backups/global/20260101-000000"
            os.makedirs(spent, exist_ok=True)
            os.makedirs(keep, exist_ok=True)
            open(f"{spent}/.verified", "w").write("ok\n")
            r = subprocess.run(
                [ZSH, "-c", sorter], capture_output=True, text=True,
                cwd=h2, env=dict(os.environ, HOME=h2, PWD=h2),
            )
            lines = {ln.split(None, 1)[0]: ln for ln in r.stdout.strip().splitlines() if ln.strip()}
            check(
                "a .verified run dir is classed spent",
                any(l.startswith("spent") and spent in l for l in r.stdout.splitlines()),
                f"output: {r.stdout.strip()!r}",
            )
            check(
                "an unmarked run dir is KEPT even though it is the older one",
                any(l.startswith("KEEP") and keep in l for l in r.stdout.splitlines()),
                "age must never substitute for the marker - the oldest dir is "
                "exactly as likely to be the failed run whose backup is the "
                f"only remaining copy; output: {r.stdout.strip()!r}",
            )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED ({len(failures)}): " + ", ".join(failures))
        return 1
    print("all backup-lifecycle checks passed")
    return 0


if __name__ == "__main__":
    print("backup lifecycle: check 7's listing recipe")
    sys.exit(main())
