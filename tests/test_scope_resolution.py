#!/usr/bin/env python3
"""Tests for the scope-resolution procedure.

Like tests/test_preservation_probe.py, these do not test prose - they execute
the procedure the prose prescribes. The project-dir encoding is the one rule in
this plugin that is a runnable command rather than a judgement call, so it is
the one rule that can be wrong in a way no reader notices: a path containing a
dot resolves to a directory that does not exist, and the failure surfaces much
later as "this project has no memory dir yet".

Run: python3 tests/test_scope_resolution.py
"""

import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(
    REPO, "skills", "notation-audit", "references", "scope-resolution.md"
)
MARKER = "<!-- canonical-encoding -->"

# (absolute path, expected ~/.claude/projects/<dir> name).
# The first two are verified against real directories on the author's machine;
# the rest pin the character classes the rule must and must not touch.
CASES = [
    ("/Users/ryanrobson/git/notation", "-Users-ryanrobson-git-notation"),
    ("/Users/ryanrobson/.claude", "-Users-ryanrobson--claude"),
    ("/Users/x/git/my.app", "-Users-x-git-my-app"),
    ("/Users/x/git/git_tutorial", "-Users-x-git-git_tutorial"),
    ("/Users/x/git/ClassCabinet-ios", "-Users-x-git-ClassCabinet-ios"),
    ("/Users/x/git/a.b.c", "-Users-x-git-a-b-c"),
]

failures = []


def check(name, condition, detail="", info=""):
    """Print one row. `detail` is FAILURE-only; `info` prints either way.

    `detail` explains what went wrong, so it is routinely phrased as the
    failure ("the two copies have drifted", "got X want Y"). Printing that on a
    passing row makes a green run read as a red one - the exact misleading
    verification output this repo exists to prevent. Anything worth showing on a
    pass (a scanned-file count, a measured byte figure) goes in `info`.
    """
    status = "ok  " if condition else "FAIL"
    suffix = info if condition else " - ".join(x for x in (info, detail) if x)
    print(f"  [{status}] {name}" + (f" - {suffix}" if suffix else ""))
    if not condition:
        failures.append(name)


def canonical_block(path):
    """Return the single ```sh block that follows the canonical-encoding marker."""
    text = open(path, encoding="utf-8").read()
    blocks = re.findall(
        re.escape(MARKER) + r"\s*\n```sh\n(.*?)\n```", text, re.DOTALL
    )
    return blocks


def run_encode(block, arg):
    """Execute the shipped block against a given cwd and read back `$enc`.

    The block must be self-contained - a single expression usable as the first
    line of any Bash invocation - because the Bash tool does not persist shell
    functions or variables between calls. So the harness only supplies the cwd
    (as $PWD) and prints whatever the block assigned.
    """
    script = 'PWD="$1"\n' + block + "\nprintf '%s' \"$enc\"\n"
    out = subprocess.run(
        ["/bin/sh", "-c", script, "sh", arg], capture_output=True, text=True
    )
    return out.stdout.strip(), out.stderr.strip()


print("scope-resolution: canonical encoding block")
blocks = canonical_block(REFERENCE)
check(
    "reference defines exactly one canonical block",
    len(blocks) == 1,
    f"found {len(blocks)}",
)

if len(blocks) == 1:
    block = blocks[0]
    check(
        "block is self-contained (no helper function)",
        "()" not in block and "encode_cwd" not in block and "enc=" in block,
        "must be inlinable at the point of use - shell state does not persist "
        "between Bash calls, so a defined-elsewhere helper is always unset",
    )
    for path, expected in CASES:
        got, err = run_encode(block, path)
        check(f"encode {path}", got == expected, f"got {got!r} want {expected!r}"
              + (f" stderr={err!r}" if err else ""))

print("\nscope-resolution: no wildcard project resolution")
# A `projects/*/memory` glob matches every project on the machine, so it can
# never identify THE current one. This test file names the pattern in order to
# ban it, so tests/ is excluded from its own scan. Every OTHER tracked file is
# scanned regardless of extension. scope-resolution.md also
# must name the pattern once, in prose, to warn against it - but that
# exemption is scoped to the ONE line that does so, not the whole file, so
# any OTHER line in scope-resolution.md that reintroduces the glob (e.g. as
# real advice added later) is still caught.
REFERENCE_REL = os.path.relpath(REFERENCE, REPO)
EXEMPT_LINE = (
    "**Never resolve with a `*` glob.** `ls -d ~/.claude/projects/*/memory` "
    "matches every"
)
tracked = subprocess.run(
    ["git", "ls-files"], cwd=REPO, capture_output=True, text=True
).stdout.split()
offenders = []
scanned = []
for rel in tracked:
    # Every tracked file, not just markdown - the glob is just as wrong in
    # scripts/verify.sh, a shipped shell script, or a .py helper as it is in
    # prose, and a .md-only scan would let it back in through any of them.
    # Same file set as the dot-less-sed ban below.
    if rel.startswith("tests/"):
        continue
    try:
        body = open(os.path.join(REPO, rel), encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    scanned.append(rel)
    for i, line in enumerate(body.splitlines(), 1):
        if re.search(r"projects/\*", line):
            if rel == REFERENCE_REL and line.strip() == EXEMPT_LINE:
                continue
            offenders.append(f"{rel}:{i}: {line.strip()}")
# Without this, an empty file list (non-git checkout, tarball, a `git ls-files`
# that failed) leaves `offenders` empty and the row above passes having read
# nothing at all. The scan must prove it reached the shipped markdown.
check(
    "the glob scan actually read the shipped files",
    len(scanned) >= 5 and REFERENCE_REL in scanned,
    info=f"scanned {len(scanned)} tracked file(s)",
)
check(
    "no shipped file resolves a project with a glob",
    not offenders,
    "; ".join(offenders),
)

print("\nscope-resolution: the dot-less sed is banned repo-wide")
# `sed 's#/#-#g'` is the original bug: it never replaces the dot, so any dotted
# path resolves to a directory that does not exist. Banned everywhere, not just
# inside the canonical blocks - adding it to a new file must fail the gate.
# scope-resolution.md must name it once, in prose, to warn against it; that
# exemption is scoped to the ONE line that does so. tests/ is excluded because
# this file has to name the pattern in order to ban it.
BROKEN_SED = "s#/#-#g"
BROKEN_SED_EXEMPT_LINE = "**Omitting the `.` replacement is the classic bug.** `sed 's#/#-#g'` maps"
broken = []
broken_scanned = []
for rel in tracked:
    if rel.startswith("tests/"):
        continue
    try:
        body = open(os.path.join(REPO, rel), encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    broken_scanned.append(rel)
    for i, line in enumerate(body.splitlines(), 1):
        if BROKEN_SED in line:
            if rel == REFERENCE_REL and line.strip() == BROKEN_SED_EXEMPT_LINE:
                continue
            broken.append(f"{rel}:{i}: {line.strip()}")
check(
    "the dot-less-sed scan actually read the repo",
    len(broken_scanned) >= 5 and REFERENCE_REL in broken_scanned,
    info=f"scanned {len(broken_scanned)} tracked file(s)",
)
check(
    "no shipped file uses the dot-less encoding",
    not broken,
    "; ".join(broken),
)

print("\nscope-resolution: no drift between copies of the canonical block")
NOTATE = os.path.join(REPO, "commands", "notate.md")
copies = canonical_block(NOTATE)
check(
    "commands/notate.md carries exactly one canonical block",
    len(copies) == 1,
    f"found {len(copies)}",
)
if len(blocks) == 1 and len(copies) == 1:
    check(
        "notate.md's block is byte-identical to the reference's",
        copies[0] == blocks[0],
        "the two copies have drifted",
    )

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    sys.exit(1)
print("all scope-resolution checks passed")
sys.exit(0)
