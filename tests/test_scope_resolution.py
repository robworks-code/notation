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

print("\nscope-resolution: every encoding call site matches the canonical one")
# The encoding cannot be a helper (shell state does not persist between Bash
# calls), so it is inlined at every point of use - currently nine of them. The
# marker-based check above only covers the two marked copies; the ban below only
# covers one historically broken literal. Neither catches a call site drifting
# into a DIFFERENTLY wrong form (`sed 's|/|-|g'`, `tr '/.' '--'`,
# `${PWD//\//-}`, or a dropped trailing `g`), which fails exactly like the
# original bug. So: find every site by a deliberately LOOSE signal, then require
# each to be byte-identical to the canonical expression.
#
# The signal must stay loose. A detector that only recognises the correct form
# would skip a drifted site instead of failing on it - a guard that passes by
# not looking. Anything mentioning the cwd, or assigning `enc`, is a candidate,
# and a candidate the extractor cannot parse is an offender rather than a skip.
#
# `\$\{?PWD` must cover the BRACED form too. Matching only `$PWD` would skip
# `dir=${PWD//\//-}` - a drift this scan specifically exists to catch - because
# it assigns no `enc` either, so nothing else would look at the line. The
# coverage row below would notice the site count dropped, but only until the
# repo legitimately gains a tenth call site, at which point the same drift ships
# green.
CANDIDATE = re.compile(r"\benc=|\$\{?PWD\b|\$\(\s*pwd|`pwd`|\bpwd\b", re.IGNORECASE)
# RHS of an `enc=` assignment: a command substitution, a parameter expansion, or
# a bare word. The `$(...)` form tolerates no nested `)`, which the canonical
# expression does not have - a site that grew one is unparseable here and is
# therefore reported, not skipped.
ASSIGN = re.compile(r"\benc=(\$\([^)]*\)|\$\{[^}]*\}|[^\s;`]+)")
canon_rhs = blocks[0].strip().split("=", 1)[1] if len(blocks) == 1 else None

# Prose that must NAME a wrong form in order to warn against it, or that
# mentions the cwd conversationally. Like the two scans above, an exemption is
# scoped to ONE exact line, never to a whole file - so any other line in the
# same file that reintroduces a bad form is still caught. Add a line here only
# when it is documentation ABOUT the encoding, never to quiet a real call site.
ENCODE_EXEMPT = {
    (
        "skills/notation-audit/references/scope-resolution.md",
        "form - another `sed` delimiter, `tr`, `${PWD//\\//-}`, a dropped trailing `g` - fails",
    ),
}

# Every file expected to carry at least one call site. Listed so that deleting a
# site (or a scan that silently reads nothing) fails instead of passing with an
# empty offender list.
EXPECTED_SITE_FILES = {
    "commands/notate.md",
    "skills/notation-audit/SKILL.md",
    "skills/notation-audit/references/scope-resolution.md",
    "skills/notation-audit/references/audit-checklist.md",
    "skills/notation-audit/references/verify-after-apply.md",
}
sites = []
drifted = []
exempted = []
for rel in tracked:
    if rel.startswith("tests/"):
        continue
    try:
        body = open(os.path.join(REPO, rel), encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    for i, line in enumerate(body.splitlines(), 1):
        if not CANDIDATE.search(line):
            continue
        if (rel, line.strip()) in ENCODE_EXEMPT:
            exempted.append((rel, line.strip()))
            continue
        found = ASSIGN.findall(line)
        if not found:
            # Mentions the cwd but assigns no `enc` - an encoding written under
            # another name, or prose that should not be naming $PWD at all.
            drifted.append(f"{rel}:{i}: unrecognized form: {line.strip()}")
            continue
        for rhs in found:
            sites.append((rel, i))
            if rhs != canon_rhs:
                drifted.append(f"{rel}:{i}: {rhs}")

site_files = {rel for rel, _ in sites}
check(
    "the call-site scan found every file expected to carry one",
    len(sites) >= 9 and EXPECTED_SITE_FILES <= site_files,
    f"found {len(sites)} site(s) in {sorted(site_files)}; "
    f"missing {sorted(EXPECTED_SITE_FILES - site_files)}",
    info=f"{len(sites)} call site(s) across {len(site_files)} file(s)",
)
# An exemption that no longer matches any line is a dead entry that would let a
# future line matching the OLD text through unnoticed - and, worse, reads as
# coverage. Require each to still be earning its keep.
check(
    "every exemption still matches a real line",
    len(exempted) == len(ENCODE_EXEMPT),
    f"{len(ENCODE_EXEMPT) - len(set(exempted))} stale exemption(s): "
    f"{sorted(ENCODE_EXEMPT - set(exempted))}",
    info=f"{len(exempted)} exempted prose line(s)",
)
# Guarded: with no single canonical block, `canon_rhs` is None and all 9 real
# sites compare unequal, burying the actual cause (the already-failing row at
# the top) under a 9-entry drift dump.
if canon_rhs is not None:
    check(
        "every call site is byte-identical to the canonical expression",
        not drifted,
        "; ".join(drifted),
    )

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    sys.exit(1)
print("all scope-resolution checks passed")
sys.exit(0)
