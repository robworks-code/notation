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
# ban it, so tests/ is excluded from its own scan. scope-resolution.md also
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
for rel in tracked:
    if rel.startswith("tests/") or not rel.endswith(".md"):
        continue
    body = open(os.path.join(REPO, rel), encoding="utf-8").read()
    for i, line in enumerate(body.splitlines(), 1):
        if re.search(r"projects/\*", line):
            if rel == REFERENCE_REL and line.strip() == EXEMPT_LINE:
                continue
            offenders.append(f"{rel}:{i}: {line.strip()}")
check(
    "no shipped file resolves a project with a glob",
    not offenders,
    "; ".join(offenders),
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
