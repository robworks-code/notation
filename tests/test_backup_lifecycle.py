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


def listing_block():
    """The ```bash block under check 7's 'List every family' heading."""
    text = open(CHECKLIST, encoding="utf-8").read()
    section = text.split("### List every family", 1)
    if len(section) != 2:
        return None
    m = re.search(r"```bash\n(.*?)\n```", section[1], re.DOTALL)
    return m.group(1) if m else None


def plant(home, project):
    """One backup per family check 7 claims to list. Returns {family: path}."""
    enc = project.replace("/", "-").replace(".", "-")
    paths = {
        # 1 config snapshot - listed, but never proposed for deletion.
        "config snapshot": f"{home}/.claude/CLAUDE.md.bak.20260730-141530",
        # 2 note run backup - the family #14/#20 found unlisted.
        "note run backup": f"{home}/.claude/notes/gcloud.md.bak.20260730-141530",
        # 3 this project's run backups.
        "project run backup": f"{home}/.claude/notation-backups/{enc}/CLAUDE.md.bak.20260730-141530",
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
    other = f"{home}/.claude/notation-backups/-Users-x-git-other"
    os.makedirs(other, exist_ok=True)
    open(f"{other}/CLAUDE.md.bak.20260101-000000", "w").write("other\n")
    return paths, other


def main():
    block = listing_block()
    check("check 7 ships one bash listing block", block is not None)
    if block is None:
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
            ["/bin/zsh", "-c", block],
            capture_output=True,
            text=True,
            cwd=project,
            env=env,
        )

        for family, path in paths.items():
            check(
                f"listing surfaces the {family}",
                path in out.stdout,
                f"{path} absent from the recipe's output",
            )

        check(
            "another project's backups are counted, not enumerated per-file",
            f"{other}/CLAUDE.md.bak.20260101-000000" not in out.stdout,
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
            ["/bin/zsh", "-c", block],
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
