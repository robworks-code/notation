#!/usr/bin/env python3
"""Tests that conflicting rules stay linked to their precedence ruling.

Three issues so far (#9, #10, #11) were the same defect: two rules in this skill
pull opposite ways and neither mentions the other, so which one wins is left to
whichever session happens to read them. Every individual rule looks correct in
isolation - that is what makes the class hard to spot in review.

The fix is structural. Each conflict gets one ruling in size-budget.md marked
`<!-- precedence-def: <id> -->`, and every rule that participates carries
`<!-- precedence-ref: <id> -->`. This test enforces that the two halves stay
connected: a ruling nothing points at is one a reader will never reach from the
rule they are actually reading, and a pointer to a ruling that no longer exists
is a dangling promise that the conflict was settled somewhere.

Run: python3 tests/test_rule_precedence.py
"""

import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF = re.compile(r"<!--\s*precedence-def:\s*([a-z0-9-]+)\s*-->")
REF = re.compile(r"<!--\s*precedence-ref:\s*([a-z0-9-]+)\s*-->")

# Conflicts that must stay documented, and every file whose rules participate in
# each. Both halves are named rather than counted: an empty repo would satisfy a
# count, and "at least one pointer from some other file" would let a conflict
# lose one of its three participating rules while still passing - the rule a
# reader is actually looking at is the one that has to carry the pointer.
BASE = "skills/notation-audit/references"
REQUIRED = {
    # Tactic 3 (append to an existing note) vs routing quality. Three rules pull
    # here: the tactic itself, the rubric's tie-breakers, and the audit check
    # that finds the drift a mis-routed append leaves behind.
    "routing-vs-index-cost": {
        f"{BASE}/size-budget.md",
        f"{BASE}/routing-rubric.md",
        f"{BASE}/audit-checklist.md",
    },
    # Check 3 (split an oversized note) vs the global no-growth budget.
    "split-vs-budget": {f"{BASE}/audit-checklist.md"},
}

failures = []


def check(name, condition, detail="", info=""):
    """Print one row. `detail` is FAILURE-only; `info` prints either way."""
    status = "ok  " if condition else "FAIL"
    suffix = info if condition else " - ".join(x for x in (info, detail) if x)
    print(f"  [{status}] {name}" + (f" - {suffix}" if suffix else ""))
    if not condition:
        failures.append(name)


tracked = subprocess.run(
    ["git", "ls-files"], cwd=REPO, capture_output=True, text=True
).stdout.split()

defs, refs, scanned = {}, {}, []
dup = []
for rel in tracked:
    if rel.startswith("tests/"):
        continue
    try:
        body = open(os.path.join(REPO, rel), encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    scanned.append(rel)
    for i, line in enumerate(body.splitlines(), 1):
        for d in DEF.findall(line):
            if d in defs:
                dup.append(f"{d} ({defs[d][0]} and {rel})")
            defs[d] = (rel, i)
        for r in REF.findall(line):
            refs.setdefault(r, []).append((rel, i))

print("rule precedence: every conflict has one ruling, reachable from both sides")
check(
    "the scan actually read the shipped files",
    len(scanned) >= 5,
    info=f"scanned {len(scanned)} tracked file(s)",
)
check(
    "every required conflict still has a ruling",
    set(REQUIRED) <= set(defs),
    f"missing ruling(s): {sorted(set(REQUIRED) - set(defs))}",
    info=f"{len(defs)} ruling(s): {sorted(defs)}",
)
check("no conflict id is defined twice", not dup, "; ".join(dup))

dangling = sorted(set(refs) - set(defs))
check(
    "every pointer resolves to a ruling",
    not dangling,
    "; ".join(f"{d} referenced from {refs[d]}" for d in dangling),
)

# A ruling is only useful if the reader reaches it from the rule they are
# reading, so EVERY participating file must carry a pointer - not just one of
# them. Checking "some other file points at it" would pass while a conflict
# quietly lost one of its sides.
missing_ptr = []
for cid, want_files in sorted(REQUIRED.items()):
    have = {f for f, _ in refs.get(cid, [])}
    for f in sorted(want_files - have):
        missing_ptr.append(f"{cid}: no pointer in {f}")
check(
    "every rule governed by a ruling points back at it",
    not missing_ptr,
    "; ".join(missing_ptr),
    info=f"{sum(len(v) for v in refs.values())} pointer(s) across "
    f"{len({f for v in refs.values() for f, _ in v})} file(s)",
)

# Separate from the declared set above: any ruling added later must still be
# reachable from somewhere other than the file that defines it.
orphan = []
for cid, (dfile, dline) in sorted(defs.items()):
    if not [f for f, _ in refs.get(cid, []) if f != dfile]:
        orphan.append(f"{cid} (defined {dfile}:{dline}, no pointer from any other file)")
check("no ruling is reachable only from its own file", not orphan, "; ".join(orphan))

print()
if failures:
    print(f"FAILED ({len(failures)}): " + ", ".join(failures))
    sys.exit(1)
print("all rule-precedence checks passed")
sys.exit(0)
