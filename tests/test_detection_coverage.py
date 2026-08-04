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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "skills", "notation-audit")
CHECKLIST = os.path.join(BASE, "references", "audit-checklist.md")
SIZE_BUDGET = os.path.join(BASE, "references", "size-budget.md")
ROUTING_RUBRIC = os.path.join(BASE, "references", "routing-rubric.md")
OUTPUT_FORMAT = os.path.join(BASE, "references", "output-format.md")

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

CITES = re.compile(r"notes/[a-z0-9-]+\.md|skill `[a-z0-9:_-]+`|skills/[a-z0-9:_-]+/")
HEADING = re.compile(r"^#+ ")

# A section that is only a trigger line plus a `Full reference: notes/x.md`
# pointer is the HEALTHY end state this checklist prescribes, and it cites a
# destination just as plainly as a full inline copy does. The floor is what
# separates the two; see the checklist's note on `min`.
MIN_SECTION_CHARS = 600

PREAMBLE = "(top of file, before the first heading)"


def self_citing_sections(claude_md_text, min_chars=MIN_SECTION_CHARS, heading_re=HEADING):
    """-> ([(chars, heading)], n_below_floor) for sections naming a destination.

    Breaks on EVERY heading level. Resetting only on `### ` folds each
    following `##` section into the preceding `###` buffer, which on a real
    file makes one section absorb the whole tail and rank first.
    """
    out, below, heading, buf = [], 0, PREAMBLE, []

    def flush():
        nonlocal below
        body = "".join(buf)
        if heading and CITES.search(body):
            if len(body) >= min_chars:
                out.append((len(body), heading))
            else:
                below += 1

    for line in claude_md_text.splitlines(keepends=True):
        if heading_re.match(line):
            flush()
            heading, buf = line.strip(), [line]
        else:
            buf.append(line)
    flush()
    return sorted(out, reverse=True), below


print("\ncase: inline section duplicating a SKILL (skills are a tier)")

# Mirrors the real defect: a long procedural section whose first line names the
# skill that already holds it. Sized past the floor, then a short `###` that
# cites nothing, then a citing `##` - the shape a `### `-only reset gets wrong,
# because the `##` body lands in the preceding `### Sudo` buffer.
FIXTURE_SKILL_DUP = (
    """# CLAUDE.md

### Verification - match the effort to the stakes

Case files: skill `verification-discipline`. It is a toolbox, not a checklist.

"""
    + "".join(f"- Rule {i}: a passing check proves nothing until seen to fail.\n" for i in range(30))
    + """
### Sudo
- Use sudo as needed.

## Plan File Management

"""
    + "".join(
        f"- Rule {i}: set Status as the last step, citing the merge SHA.\n" for i in range(18)
    )
    + "\nLayout, template, and the relocation rule: `notes/plan-files.md`\n"
)

found, below = self_citing_sections(FIXTURE_SKILL_DUP)
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

# The regression the awk had: `### Sudo` is the last `###` in the file, so a
# `### `-only reset appends the entire `## Topical Notes Index` to it. Sudo
# cites nothing, so the mis-attributed section would have surfaced only via its
# absorbed tail - and any `###` that DOES cite would be ranked on borrowed size.
sudo_size = next((c for c, h in found if "Sudo" in h), 0)
check(
    "a following `##` section is not absorbed into the preceding `###`",
    sudo_size == 0,
    detail=f"`### Sudo` measured {sudo_size} chars - it swallowed the `##` section below it",
)

# `sudo_size == 0` is trivially true whenever `Sudo` is simply absent from the
# results, so it only has teeth if the buggy form would put it there - i.e. if
# the absorbed section clears the floor by a comfortable margin. Assert that
# directly against the old `### `-only pattern, so trimming the fixture can
# never quietly turn the regression check into a no-op that still prints ok.
buggy, _ = self_citing_sections(FIXTURE_SKILL_DUP, heading_re=re.compile(r"^### "))
buggy_sudo = next((c for c, h in buggy if "Sudo" in h), 0)
check(
    "the fixture still reproduces the bug, with margin over the floor",
    buggy_sudo >= MIN_SECTION_CHARS + 300,
    info=f"`### Sudo` absorbs {buggy_sudo} chars under the `### `-only form (floor {MIN_SECTION_CHARS})",
    detail="the fixture shrank - the check above would pass even with the bug present",
)

print("\ncase: `##` sections and the preamble are their own units")

FIXTURE_H2_ONLY = """Plans live in the project's `.claude/plans/` directory, never the global one.
The template and the archiving rule are in `notes/plan-files.md` - read it
before creating or archiving any plan file, and set Status as the last step.

## Plan File Management

Plans live in the project's `.claude/plans/` - NOT the global dir - named
`YYYY-MM-DD_slug.md`, and archived once the work is committed and verified.
Set Status as the last step before the move, citing the merge SHA; it is the
only field that ages, and it rots into a lie otherwise. Abandoned is a real
outcome and should be recorded rather than filed as complete.

Directory layout, the plan-file template, and the rule for relocating an
auto-generated plan out of the global plans dir: `notes/plan-files.md`
"""

h2_found, _ = self_citing_sections(FIXTURE_H2_ONLY, min_chars=200)
h2_headings = [h for _, h in h2_found]
check(
    "a `##`-level section that cites a destination is detected",
    any("Plan File Management" in h for h in h2_headings),
    detail=f"found {h2_headings} - `##` sections are invisible to a `### `-only reset",
)
check(
    "content before the first heading is a testable unit, not skipped",
    any(h == PREAMBLE for h in h2_headings),
    detail=f"found {h2_headings} - the preamble was never buffered",
)

print("\ncase: the healthy trigger+pointer shape is not flagged")

FIXTURE_ALREADY_RELOCATED = """# CLAUDE.md

### Python on macOS
- `pip3 install <pkg>` is PEP 668-blocked - use `--break-system-packages`.
- Full reference (the sys.path trap, brew 3.14 vs 3.9.6): `notes/python-macos.md`

### Oversized tool results
- Oversized tool result -> grep the saved file, do not retry blind. Output over
  the token cap is auto-saved. Cases: `notes/claude-code-internals.md`
"""

healthy, healthy_below = self_citing_sections(FIXTURE_ALREADY_RELOCATED)
check(
    "a two-line trigger+pointer section is below the floor, not reported",
    healthy == [],
    detail=f"flagged {[h for _, h in healthy]} - the detector fires on the correct end state",
)
check(
    "sections under the floor are counted, never silently dropped",
    healthy_below == 2,
    info=f"{healthy_below} citing section(s) below the floor",
    detail="an empty result would be indistinguishable from a detector that failed",
)

# The skill reference must be recognised specifically - a note-only pattern
# would miss every procedural duplicate, which is the bug this commit fixes.
check(
    "a skill reference counts, not just a notes/ path",
    bool(CITES.search("Case files: skill `verification-discipline`.")),
    detail="skill-by-name is not matched, so procedures stay invisible",
)
# Plugin skills are named `plugin:skill`, which is how Claude Code refers to
# them and how an inline section would cite one. A slug class with no `:`
# skips exactly the sections this detector was added for.
check(
    "a QUALIFIED plugin skill name counts",
    bool(CITES.search("Full procedure: skill `superpowers:brainstorming`.")),
    detail="`plugin:skill` is unmatched, so plugin duplicates are invisible",
)
check(
    "a skills/ path counts as a citation too",
    bool(CITES.search("Steps live in ~/.claude/skills/verification-discipline/SKILL.md")),
    detail="a section naming the file rather than the skill is the same citation",
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

# The label is `[^\]]+`, NOT a slug class. Real index labels carry capitals
# and spaces (`- [1Password CLI](notes/1password-cli.md)`); a slug-shaped
# pattern fails to match those lines at all, so they are counted as neither
# compressed nor skipped and a drifted index reports a clean `skipped 0`.
LINK_FORM = re.compile(r"^- \[([^\]]+)\]\(notes/([a-z0-9-]+)\.md\)")


def normalise_label(label):
    return re.sub(r"[\s_]+", "-", label.lower())


def compress_index_line(line):
    """Drop the link syntax, but ONLY where the name is recoverable.

    Link text and filename are independent. Compressing
    `- [claude-code](notes/claude-code-internals.md)` to `- claude-code`
    destroys the path, which is the opposite of the loss-free saving claimed.
    """
    m = LINK_FORM.match(line)
    if not m or normalise_label(m.group(1)) != m.group(2):
        return line
    return LINK_FORM.sub(f"- {m.group(2)}", line, count=1)


def compress_index_section(section_lines):
    """-> (rewritten section, current, compressed, skipped).

    EVERY line is returned, not just the entries: blank lines, the convention
    paragraph, and entries already in bare form pass through untouched. The
    output is the rewritten section, so an auditor can diff it and paste it
    back. Filtering to matching lines would make it a truncated index - a
    deletion, in the one check whose premise is that it loses nothing. The
    char totals cover the entries only, which is what encoding cost is.
    """
    rewritten, current, compressed, skipped = [], 0, 0, 0
    for line in section_lines:
        m = LINK_FORM.match(line)
        if not m:
            rewritten.append(line)
            continue
        new = compress_index_line(line)
        current += len(line) + 1
        compressed += len(new) + 1
        if new == line:
            skipped += 1
        rewritten.append(new)
    return rewritten, current, compressed, skipped


print("\ncase: index waste that no length cap can see")

# Every line here is comfortably under 100 chars, so the hook-length check
# correctly reports nothing. The waste is entirely in the link syntax.
#
# Three of them label a note with something other than its filename - the real
# index does this, and it is the one shape where naive compression loses the
# path. A fixture built only from matching pairs cannot fail on that bug.
FIXTURE_INDEX = [
    f"- [topic-{i:03d}](notes/topic-{i:03d}.md) - short routing hook for topic {i}"
    for i in range(100)
]
MISLABELLED = {
    7: "- [claude-code](notes/claude-code-internals.md) - plugin install, hooks",
    23: "- [gh](notes/gh-git.md) - gh CLI and git: merges, stacked PRs, squash",
    64: "- [zsh](notes/zsh-scripting.md) - zsh script traps: cp -R, glob replace",
}
# Labels with capitals and spaces: these ARE recoverable (normalise and the
# slug falls out), so they must compress rather than be silently unmatched.
CASED = {
    11: "- [1Password CLI](notes/1password-cli.md) - op read for secrets, SSH agent",
    42: "- [Gcloud](notes/gcloud.md) - gcloud CLI reference: components, accounts",
}
for i, line in {**MISLABELLED, **CASED}.items():
    FIXTURE_INDEX[i] = line

# The section is not only entries. These must survive the rewrite untouched -
# the convention line is the one the checklist tells you to ADD.
FIXTURE_SECTION = (
    ["Detailed notes live under `~/.claude/notes/` - each entry below is <name>.md there.", ""]
    + FIXTURE_INDEX
    + ["", "- already-bare - an entry someone compressed by hand earlier"]
)

longest = max(len(l) for l in FIXTURE_INDEX)
section_out, current, compressed, skipped = compress_index_section(FIXTURE_SECTION)
rewritten = [compress_index_line(l) for l in FIXTURE_INDEX]

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
    "compression is loss-free: every note PATH is still derivable",
    all(
        f"notes/{new.split(' - ')[0][2:]}.md" in orig
        for orig, new in zip(FIXTURE_INDEX, rewritten)
        if new != orig
    ),
    detail="the rewrite kept a label whose filename can no longer be recovered",
)
check(
    "a line whose label differs from its filename is left in link form",
    all(rewritten[i] == line for i, line in MISLABELLED.items()),
    detail=f"rewrote {[rewritten[i] for i in MISLABELLED if rewritten[i] != FIXTURE_INDEX[i]]}",
)
check(
    "those lines are reported as skipped, not counted as savings",
    skipped == len(MISLABELLED),
    info=f"skipped {skipped}",
    detail="a silent skip reads as a healthy index",
)
check(
    "and the line count is unchanged",
    len(rewritten) == len(FIXTURE_INDEX),
)

check(
    "a label with capitals and spaces still compresses",
    all(
        rewritten[i].startswith(f"- {slug} -")
        for i in CASED
        # Read the slug off the path directly, so a label pattern that fails to
        # match these lines reports a clean FAIL rather than crashing here.
        for slug in [FIXTURE_INDEX[i].split("(notes/")[1].split(".md)")[0]]
    ),
    detail=f"left as {[rewritten[i] for i in CASED]} - a slug-shaped label pattern skips these",
)
check(
    "and is NOT miscounted as skipped",
    skipped == len(MISLABELLED),
    info=f"skipped {skipped}",
    detail="cased labels inflate the skip count, or vanish from both totals",
)

print("\ncase: the rewritten output is the whole section, not just the entries")

check(
    "every input line comes back, entry or not",
    len(section_out) == len(FIXTURE_SECTION),
    info=f"{len(FIXTURE_SECTION)} in, {len(section_out)} out",
    detail="filtering to entries turns the scratch file into a truncated index",
)
check(
    "the convention paragraph the checklist tells you to add survives",
    any("each entry below is <name>.md there" in l for l in section_out),
    detail="pasting the output back would delete the line that makes bare form legible",
)
check(
    "an entry already in bare form survives",
    any(l.startswith("- already-bare ") for l in section_out),
    detail="a partially compressed index loses its compressed entries",
)
check(
    "blank lines survive",
    section_out.count("") == FIXTURE_SECTION.count(""),
)
check(
    "the char totals still cover the entries only",
    current == sum(len(l) + 1 for l in FIXTURE_INDEX),
    detail="non-entry lines leaked into the encoding-cost measurement",
)

check(
    "the checklist documents encoding cost separately from hook length",
    "Index encoding cost" in checklist and "BEFORE hook length" in checklist,
    detail="only hook length is documented, so a link-form index reads as healthy",
)


# --------------------------------------------------------------------------
# Detector: the relocation breadcrumb.
#
# A note section headed "(relocated from CLAUDE.md)" is a CLAIM that the move
# completed. If the moved text is still in CLAUDE.md, the append succeeded and
# the removal did not - a proven duplicate, not a suspected one.
# --------------------------------------------------------------------------

BREADCRUMB = re.compile(r"^#+ .*relocated from CLAUDE\.md")


def relocated_sections(body):
    """-> [(heading, [body lines])] for each breadcrumbed section of a note.

    A note holds several sections and usually only one claims a relocation.
    The section ends at the next heading of any level.
    """
    out, current = [], None
    for line in body.splitlines():
        if HEADING.match(line):
            current = [line.strip(), []] if BREADCRUMB.match(line) else None
            if current:
                out.append(current)
        elif current:
            current[1].append(line)
    return [(h, lines) for h, lines in out]


def stale_relocations(claude_md_text, note_texts):
    """-> [(note, heading, probe)] where a relocated section is still inline."""
    stale = []
    for name, body in note_texts.items():
        for heading, lines in relocated_sections(body):
            for line in lines:
                line = line.strip()
                # A distinctive line: long enough not to collide by accident.
                if len(line) > 40 and not line.startswith("#") and line in claude_md_text:
                    stale.append((name, heading, line))
                    break
    return stale


print("\ncase: a relocation that appended but never removed")

CLAUDE_WITH_LEFTOVER = """# CLAUDE.md

### PATH clobbering
The clobber is inherited by every child process, so a test shelling out fails.

### Something else
Nothing relocated about this one.
"""

NOTES = {
    # Claims the move happened; its text is still inline above.
    "macos-platform.md": """# macOS platform

## The PATH clobber (relocated from CLAUDE.md 2026-08-04)
The clobber is inherited by every child process, so a test shelling out fails.
""",
    # A healthy note: relocated, and the source really was cleaned.
    "zsh-scripting.md": """# zsh scripting

## Glob traps (relocated from CLAUDE.md 2026-07-30)
An unquoted glob matching no file aborts the whole command chain in zsh.
""",
    # No breadcrumb at all - must not be probed.
    "railway.md": """# Railway

## Auth
The clobber is inherited by every child process, so a test shelling out fails.
""",
    # Breadcrumbed AND clean, but an unrelated section of the same note happens
    # to repeat a line that is still inline. Probing the whole note body reports
    # this as a stale relocation and points the auditor at the wrong section.
    "python-macos.md": """# Python on macOS

## PEP 668 (relocated from CLAUDE.md 2026-07-12)
pip3 install is blocked; pass --break-system-packages to install anyway.

## Why brew python
The clobber is inherited by every child process, so a test shelling out fails.
""",
}

stale = stale_relocations(CLAUDE_WITH_LEFTOVER, NOTES)
names = [n for n, _, _ in stale]

check(
    "flags the note whose relocated text is still inline",
    "macos-platform.md" in names,
    detail=f"flagged {names}",
)
check(
    "the probe names the relocated section it came from",
    any(n == "macos-platform.md" and "PATH clobber" in h for n, h, _ in stale),
    detail=f"reported {[(n, h) for n, h, _ in stale]}",
)
check(
    "does not flag a relocation that really was removed",
    "zsh-scripting.md" not in names,
    detail="false positive on a healthy relocation",
)
check(
    "does not probe a note with no relocation breadcrumb",
    "railway.md" not in names,
    info="even though its text also appears inline",
    detail="probing every note produces noise and false duplicates",
)
check(
    "probes only the relocated section, not the rest of the note",
    "python-macos.md" not in names,
    info="its clean relocation sits beside an unrelated matching line",
    detail="a whole-body probe reports a stale relocation on unrelated text",
)


# --------------------------------------------------------------------------
# Divergence: two tiers, same subject, incompatible claims.
# --------------------------------------------------------------------------

print("\ncase: divergence outranks duplication")

check(
    "check 5 tells the auditor to look for contradictions, not just copies",
    "Divergence is worse than duplication" in checklist,
    detail="only duplication is modelled, so a contradiction survives the audit",
)
check(
    "and rules that the newer dated measurement wins",
    "always outranks an undated assertion" in checklist,
    detail="no tie-break, so the auditor must guess which copy is right",
)
check(
    "the checklist prescribes mechanical detectors, not eyeballing",
    "Do not eyeball this" in checklist and "relocated from CLAUDE.md" in checklist,
    detail="check 5 stays a search nobody performs",
)


# --------------------------------------------------------------------------
# Doc-side drift: the checklist owns the wording, this file owns the
# behaviour. These assert the published commands carry the same invariants the
# reimplementations above are tested on.
# --------------------------------------------------------------------------

print("\ncase: the published commands carry the tested invariants")

check(
    "the section detector breaks on every heading level",
    "/^#+ /{ flush(); h=$0" in checklist,
    detail="a `### `-only reset folds each following `##` into the previous section",
)
check(
    "it seeds a heading so the preamble is testable",
    'BEGIN{h="(top of file' in checklist,
    detail="content before the first heading is never buffered",
)
check(
    "it applies a size floor and reports what fell below it",
    "-v min=" in checklist and "if(c>=min)" in checklist and "below++" in checklist,
    detail="without a floor it fires on the healthy trigger+pointer shape",
)
check(
    "the below-floor count goes to stderr rather than being dropped",
    'not shown)\\n", below, min > "/dev/stderr"' in checklist,
    detail="a silent drop makes a healthy setup look like a failed detector",
)
check(
    "the breadcrumb grep is heading-anchored",
    "grep -rlE '^#+ .*relocated from CLAUDE\\.md'" in checklist,
    detail="unanchored, it matches prose that merely discusses relocation",
)
check(
    "it passes directories rather than globbing SKILL.md",
    "~/.claude/notes ~/.claude/skills ~/.claude/plugins 2>/dev/null" in checklist
    and not any(
        l.lstrip().startswith("grep") and "skills/*/" in l for l in checklist.splitlines()
    ),
    detail="an unmatched zsh glob aborts the command before grep runs",
)
check(
    "the index compressor captures the name from the path, guarded",
    "$norm eq $slug" in checklist and r"\(notes\/([a-z0-9-]+)\.md\)" in checklist,
    detail="capturing the link text destroys the path when the two differ",
)
check(
    "and reports skipped lines rather than silently keeping them",
    "skipped %d" in checklist,
    detail="a skip that is not counted reads as a clean compression",
)
check(
    "it matches labels as [^\\]]+, not a slug class",
    r"^- \[([^\]]+)\]" in checklist and "[\\s_]+" in checklist,
    detail="capitalised or spaced labels are unmatched and report a false `skipped 0`",
)
check(
    "it prints every line of the section, not only the entries",
    "next unless" not in checklist and "Every line of the section is printed" in checklist,
    detail="the scratch file becomes a truncated index and pasting it back deletes entries",
)
check(
    "the citation pattern admits a qualified plugin skill name",
    "skill `[a-z0-9:_-]+`" in checklist,
    detail="`plugin:skill` is how Claude Code names them, and it would not match",
)
check(
    "the breadcrumb search covers plugin skills",
    "~/.claude/plugins" in checklist,
    detail="a section relocated into a plugin skill leaves an unreachable breadcrumb",
)

core_constants = open(
    os.path.join(REPO, "scripts", "notation_core", "constants.py"), encoding="utf-8"
).read()
notate = open(os.path.join(REPO, "commands", "notate.md"), encoding="utf-8").read()
notate_all = open(os.path.join(REPO, "commands", "notate-all.md"), encoding="utf-8").read()

check(
    "thresholds are defined in the core",
    "INLINE_MAX = 200" in core_constants and "JUSTIFY_MAX = 600" in core_constants,
    detail="the single source of the routing bands is missing",
)
check(
    "and the command docs do not restate them",
    not re.search(r"\b(200|600|40,?000|20,?000)\b", notate + notate_all),
    detail="a threshold change would leave the command docs disagreeing with the gate",
)
check(
    "the capture commands run the gate before writing",
    'notation-core.py" gate' in notate and 'notation-core.py" gate' in notate_all,
    detail="a capture that never gates is the state this core exists to replace",
)
check(
    "notate-all says the gate is not optional",
    "The gate is not optional here" in notate_all,
    detail="it applies everything with no picker, so nothing else catches a bad run",
)
check(
    "the audit skill defers to the core for sizes",
    'notation-core.py" measure' in checklist,
    detail="audit and capture computing sizes separately is how they drift",
)
check(
    "and the audit reference docs do not restate the thresholds either",
    not re.search(
        r"\b(200|600|40,?000|20,?000)\b",
        checklist + open(SIZE_BUDGET, encoding="utf-8").read()
        + open(ROUTING_RUBRIC, encoding="utf-8").read()
        + open(OUTPUT_FORMAT, encoding="utf-8").read(),
    ),
    detail="a band change would leave the audit skill's own docs disagreeing with the gate",
)


# --------------------------------------------------------------------------
# Contract: a skill is a destination the report format has to be able to
# express. A tier the router can send content to, but the ledger cannot label
# and the budget has no delta method for, is a dead end at apply time.
# --------------------------------------------------------------------------

print("\ncase: skill is a first-class destination end to end")

rubric = open(os.path.join(BASE, "references", "routing-rubric.md"), encoding="utf-8").read()
budget = open(os.path.join(BASE, "references", "size-budget.md"), encoding="utf-8").read()
out_fmt = open(os.path.join(BASE, "references", "output-format.md"), encoding="utf-8").read()

check(
    "the rubric's skill rule is a valid ordered-list item",
    "2b." not in rubric and "3. **Is it a PROCEDURE" in rubric,
    detail="`2b.` is not an ordered-list marker, so it renders outside the tree",
)
check(
    "the rubric states which rule wins for a tool-tied procedure",
    "<!-- precedence-def: procedure-vs-surface -->" in rubric,
    detail="rule 2 lists 'one CLI's auth flow' as a note; two sessions route it differently",
)
check(
    "the budget has a delta method for a skill move",
    "9. Section -> skill" in budget,
    detail="a proposed skill move has no formula, so its row cannot be computed",
)
check(
    "and says a skill costs no index line",
    "No index line" in budget,
    detail="tactic 1's index-line term would be applied to a destination that has none",
)
check(
    "the budget no longer claims all tactics move into notes/",
    "These seven tactics" not in budget and "These nine tactics" in budget,
    detail="the tactic count and destination claim contradict the skill tactic",
)
check(
    "the measured/estimated rule covers the new tactics",
    "Tactics 4, 6 and 8" in budget and "1, 2, 3, 7 and 9" in budget,
    detail="a tactic outside the enumeration has no rule for the `~` marker",
)
check(
    "encoding cost and the hook cap state which one measures first",
    "<!-- precedence-def: encoding-vs-cap -->" in budget,
    detail="both count the same link-syntax bytes into the gated `global` bucket",
)
check(
    "the report format can label a skill row",
    "- `skill` - `~/.claude/skills/<name>/SKILL.md`" in out_fmt
    and "has **four** values" in out_fmt,
    detail="a skill move has no valid `file` value and folds into the notes-only ledger line",
)


print()
if failures:
    print(f"DETECTION COVERAGE FAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("all detection-coverage checks passed")
