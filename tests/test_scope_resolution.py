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


def check(name, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
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
    """Execute the shipped block, then call the function it defines."""
    script = block + '\nencode_cwd "$1"\n'
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
        "block defines encode_cwd",
        "encode_cwd()" in block,
        "the function name other files copy verbatim",
    )
    for path, expected in CASES:
        got, err = run_encode(block, path)
        check(f"encode {path}", got == expected, f"got {got!r} want {expected!r}"
              + (f" stderr={err!r}" if err else ""))

print("\nscope-resolution: no wildcard project resolution")
# A `projects/*/memory` glob matches every project on the machine, so it can
# never identify THE current one. This test file names the pattern in order to
# ban it, so tests/ is excluded from its own scan - and scope-resolution.md is
# excluded too, since it must name the same anti-pattern in prose to warn
# against it (see its "Never resolve with a `*` glob" paragraph).
REFERENCE_REL = os.path.relpath(REFERENCE, REPO)
tracked = subprocess.run(
    ["git", "ls-files"], cwd=REPO, capture_output=True, text=True
).stdout.split()
offenders = []
for rel in tracked:
    if rel.startswith("tests/") or rel == REFERENCE_REL or not rel.endswith(".md"):
        continue
    body = open(os.path.join(REPO, rel), encoding="utf-8").read()
    for i, line in enumerate(body.splitlines(), 1):
        if re.search(r"projects/\*", line):
            offenders.append(f"{rel}:{i}: {line.strip()}")
check(
    "no shipped file resolves a project with a glob",
    not offenders,
    "; ".join(offenders),
)

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    sys.exit(1)
print("all scope-resolution checks passed")
sys.exit(0)
