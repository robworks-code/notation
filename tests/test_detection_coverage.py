#!/usr/bin/env python3
"""Tests that the audit's DETECTORS fire on the cases they were written for.

The checklist's find-it rules are prose, so nothing stops one from being
technically true and operationally useless - it runs, reports nothing, and the
run looks clean. That failure is silent and indistinguishable from a healthy
setup, which is exactly how a real 41,327-char CLAUDE.md survived an audit with
no findings on 2026-08-04.

Each case below plants a defect the checklist claims to catch, runs the
detector logic against the fixture, and asserts it fires. The detectors are
reimplemented here rather than scraped out of the markdown: the checklist owns
the wording, this file owns the behaviour, and a doc-side check keeps the two
from drifting apart silently.

Run: python3 tests/test_detection_coverage.py
"""

import os
import re
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "skills", "notation-audit")
CHECKLIST = os.path.join(BASE, "references", "audit-checklist.md")

failures = []


def check(name, condition, detail="", info=""):
    """Print one row. `detail` is FAILURE-only; `info` prints either way."""
    status = "ok  " if condition else "FAIL"
    suffix = info if condition else " - ".join(x for x in (info, detail) if x)
    print(f"  [{status}] {name}" + (f" - {suffix}" if suffix else ""))
    if not condition:
        failures.append(name)


# --------------------------------------------------------------------------
# Detector: an inline section that names its own relocation destination.
#
# A CLAUDE.md subsection citing `notes/x.md` or a skill by name is
# self-identifying: something already decided where this belongs. Rank by
# section size, because the cost of leaving it inline scales with it.
# --------------------------------------------------------------------------

CITES = re.compile(r"notes/[a-z0-9-]+\.md|skill `[a-z0-9-]+`")


def self_citing_sections(claude_md_text):
    """-> [(chars, heading)] for each `###` section that names a destination."""
    out, heading, buf = [], None, []
    for line in claude_md_text.splitlines(keepends=True):
        if line.startswith("### "):
            if heading and CITES.search("".join(buf)):
                out.append((len("".join(buf)), heading))
            heading, buf = line.strip(), [line]
        elif heading:
            buf.append(line)
    if heading and CITES.search("".join(buf)):
        out.append((len("".join(buf)), heading))
    return sorted(out, reverse=True)


print("\ncase: inline section duplicating a SKILL (skills are a tier)")

# Mirrors the real defect: a long procedural section whose first line names the
# skill that already holds it. Padded past a trivial length so the size ranking
# is meaningful rather than incidental.
FIXTURE_SKILL_DUP = """# CLAUDE.md

### Verification - match the effort to the stakes

Case files: skill `verification-discipline`. It is a toolbox, not a checklist.

- Pick the proof and say which you used.
- A passing check proves nothing until you have seen it fail.
- If you do run a mutation matrix, check the guard SET.
- The thing answering you is not always the thing you changed.

### Sudo
- Use sudo as needed.
"""

found = self_citing_sections(FIXTURE_SKILL_DUP)
check(
    "detector finds the section that names its own skill",
    any("Verification" in h for _, h in found),
    detail=f"found {[h for _, h in found]}",
)
check(
    "it is ranked first by size, ahead of the short section",
    bool(found) and "Verification" in found[0][1],
    info=f"top section is {found[0][1] if found else 'none'} at {found[0][0] if found else 0} chars",
)
check(
    "a section citing NO destination is not flagged",
    all("Sudo" not in h for _, h in found),
)

# The skill reference must be recognised specifically - a note-only pattern
# would miss every procedural duplicate, which is the bug this commit fixes.
check(
    "a skill reference counts, not just a notes/ path",
    bool(CITES.search("Case files: skill `verification-discipline`.")),
    detail="skill-by-name is not matched, so procedures stay invisible",
)


print("\ncase: the checklist documents skills as a tier")

checklist = open(CHECKLIST, encoding="utf-8").read()
skill_doc = open(os.path.join(BASE, "SKILL.md"), encoding="utf-8").read()

check(
    "SKILL.md lists skills among the tiers",
    "~/.claude/skills/<name>/SKILL.md" in skill_doc,
    detail="tier list does not mention skills, so check 5 cannot compare against them",
)
check(
    "check 1 offers a skill as a destination for procedures",
    "the destination is a **skill**" in checklist,
    detail="check 1 only ever proposes notes/, so a procedure has nowhere correct to go",
)
check(
    "check 5 counts skills as a tier",
    "Skills count as a tier here" in checklist,
    detail="cross-tier duplication cannot fire on a skill",
)


# --------------------------------------------------------------------------
# Detector: index encoding cost.
#
# The pre-existing check measured how many index lines exceed a length cap. A
# per-line CONSTANT is invisible to that: every line can sit under the cap while
# the section wastes thousands of chars on link syntax. This is the regression
# to hold - a fixture where hook-length finds nothing and encoding finds plenty.
# --------------------------------------------------------------------------

LINK_FORM = re.compile(r"^- \[([a-z0-9-]+)\]\(notes/[a-z0-9-]+\.md\)")


def encoding_saving(index_lines):
    """-> (current, compressed) chars for the index in link form vs bare form."""
    current = sum(len(l) + 1 for l in index_lines)
    compressed = sum(len(LINK_FORM.sub(r"- \1", l)) + 1 for l in index_lines)
    return current, compressed


print("\ncase: index waste that no length cap can see")

# Every line here is comfortably under 100 chars, so the hook-length check
# correctly reports nothing. The waste is entirely in the link syntax.
FIXTURE_INDEX = [
    f"- [topic-{i:03d}](notes/topic-{i:03d}.md) - short routing hook for topic {i}"
    for i in range(100)
]

longest = max(len(l) for l in FIXTURE_INDEX)
current, compressed = encoding_saving(FIXTURE_INDEX)

check(
    "every fixture line is under the ~100-char hook cap",
    longest < 100,
    info=f"longest line is {longest} chars",
)
check(
    "so a length-cap check finds nothing here",
    sum(1 for l in FIXTURE_INDEX if len(l) > 100) == 0,
)
check(
    "but the encoding check finds a real saving",
    current - compressed > 2000,
    info=f"{current} -> {compressed}, saved {current - compressed}",
    detail="encoding waste went undetected",
)
check(
    "compression is loss-free: every note name survives",
    all(
        f"topic-{i:03d}" in LINK_FORM.sub(r"- \1", FIXTURE_INDEX[i]) for i in range(100)
    ),
    detail="a name was dropped by the rewrite",
)
check(
    "and the line count is unchanged",
    len([LINK_FORM.sub(r"- \1", l) for l in FIXTURE_INDEX]) == len(FIXTURE_INDEX),
)

check(
    "the checklist documents encoding cost separately from hook length",
    "Index encoding cost" in checklist and "BEFORE hook length" in checklist,
    detail="only hook length is documented, so a link-form index reads as healthy",
)


print()
if failures:
    print(f"DETECTION COVERAGE FAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("all detection-coverage checks passed")
