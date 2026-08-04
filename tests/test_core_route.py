#!/usr/bin/env python3
"""Routing bands, and the false-zero rule for candidate search.

`candidates: []` is ambiguous on its own: it means both "searched 87 notes,
none matched" and "searched 0 because the path was wrong". The second would
silently license minting a new note every single time.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import constants, route

print("\ncase: size bands")

check("a short fact is inline", route.band("x" * 50) == "inline")
check("exactly INLINE_MAX is still inline", route.band("x" * constants.INLINE_MAX) == "inline")
check("one over INLINE_MAX needs a reason", route.band("x" * (constants.INLINE_MAX + 1)) == "justify")
check("exactly JUSTIFY_MAX still justifies", route.band("x" * constants.JUSTIFY_MAX) == "justify")
check("one over JUSTIFY_MAX must become a note", route.band("x" * (constants.JUSTIFY_MAX + 1)) == "must_note")

check(
    "only the justify band asks for a reason",
    route.route("x" * 50, "~/.claude/CLAUDE.md", "/nonexistent")["requires_reason"] is False
    and route.route("x" * (constants.INLINE_MAX + 1), "~/.claude/CLAUDE.md", "/nonexistent")["requires_reason"] is True,
)

print("\ncase: candidate ranking is explainable")

with tempfile.TemporaryDirectory() as d:
    notes = os.path.join(d, "notes")
    os.makedirs(notes)
    with open(os.path.join(notes, "railway.md"), "w", encoding="utf-8") as fh:
        fh.write("# Railway\n\n## Auth\nRailway CLI auth uses a project token.\n")
    with open(os.path.join(notes, "pinecone.md"), "w", encoding="utf-8") as fh:
        fh.write("# Pinecone\n\n## Indexes\nThe pc CLI moved from a tap to a cask.\n")

    r = route.rank_notes("Railway bucket TTL must be set at create time", notes)
    check("searched every note", r["notes_searched"] == 2, info="{}".format(r["notes_searched"]))
    check("ranks the topical note first", r["candidates"][0]["path"].endswith("railway.md"),
          detail="got {}".format([c["path"] for c in r["candidates"]]))
    check(
        "and says WHICH tokens matched",
        "railway" in r["candidates"][0]["matched_tokens"],
        detail="a score with no reason cannot support a justified miss",
    )

print("\ncase: a zero says what it searched")

with tempfile.TemporaryDirectory() as d:
    empty = os.path.join(d, "notes")
    os.makedirs(empty)
    r_empty = route.rank_notes("anything", empty)
    r_missing = route.rank_notes("anything", os.path.join(d, "does-not-exist"))

    check("an empty notes dir reports it exists", r_empty["notes_dir_exists"] is True)
    check("a missing notes dir reports it does NOT exist", r_missing["notes_dir_exists"] is False)
    check(
        "the two zeros are distinguishable",
        r_empty != r_missing,
        detail="identical JSON for 'none matched' and 'searched nothing' is the false-zero bug",
    )
    check("both report zero searched", r_empty["notes_searched"] == 0 and r_missing["notes_searched"] == 0)

report("core-route")
