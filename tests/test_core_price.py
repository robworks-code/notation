#!/usr/bin/env python3
"""Signed, bucketed deltas measured from both sides.

The budget rules say measure what leaves and DRAFT what replaces. A price with
no drafted replacement is a guess, so the core refuses to produce one.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import price

HOME = os.path.expanduser("~")

with tempfile.TemporaryDirectory() as d:
    removed = os.path.join(d, "removed.txt")
    added = os.path.join(d, "added.txt")
    with open(removed, "w", encoding="utf-8") as fh:
        fh.write("x" * 1000)
    with open(added, "w", encoding="utf-8") as fh:
        fh.write("y" * 120)

    print("\ncase: a relocation prices negative")
    p = price.price(removed, added, os.path.join(HOME, ".claude", "CLAUDE.md"))
    check("delta is added minus removed", p["delta"] == 120 - 1000, info="{}".format(p["delta"]))
    check("bucket comes from the target", p["bucket"] == "global")
    check("and the global bucket is gated", p["gated"] is True)

    print("\ncase: a note target is not gated")
    p2 = price.price(removed, added, os.path.join(HOME, ".claude", "notes", "x.md"))
    check("bucket is notes", p2["bucket"] == "notes")
    check("notes never feed the gate", p2["gated"] is False)

    print("\ncase: an undrafted replacement is refused")
    raised = False
    try:
        price.price(removed, None, os.path.join(HOME, ".claude", "CLAUDE.md"))
    except ValueError:
        raised = True
    check(
        "pricing without a drafted replacement raises",
        raised,
        detail="it would return a guess indistinguishable from a measurement",
    )

    print("\ncase: a pure addition prices positive")
    empty = os.path.join(d, "empty.txt")
    open(empty, "w").close()
    p3 = price.price(empty, added, os.path.join(HOME, ".claude", "CLAUDE.md"))
    check("delta is the added size", p3["delta"] == 120, info="{}".format(p3["delta"]))

    print("\ncase: empty string added_path raises")
    raised_empty = False
    try:
        price.price(removed, "", os.path.join(HOME, ".claude", "CLAUDE.md"))
    except ValueError:
        raised_empty = True
    check(
        "empty string added_path is refused",
        raised_empty,
        detail="empty string means no draft",
    )

    print("\ncase: nonexistent added_path raises")
    raised_nonexistent = False
    try:
        price.price(removed, "/nonexistent/path.txt", os.path.join(HOME, ".claude", "CLAUDE.md"))
    except ValueError:
        raised_nonexistent = True
    check(
        "nonexistent added_path is refused",
        raised_nonexistent,
        detail="missing file means no draft",
    )

    print("\ncase: existing empty file prices as legitimate zero")
    empty_file = os.path.join(d, "empty_draft.txt")
    open(empty_file, "w").close()
    p_empty = price.price(removed, empty_file, os.path.join(HOME, ".claude", "CLAUDE.md"))
    check(
        "existing empty file is a valid draft",
        p_empty["delta"] == -1000,
        detail="should be 0 - 1000, not a raise",
        info="{}".format(p_empty["delta"]),
    )

    print("\ncase: skill bucket is not gated")
    p_skill = price.price(removed, added, os.path.join(HOME, ".claude", "skills", "x.md"))
    check("skill bucket exists", p_skill["bucket"] == "skill")
    check("skill is not gated", p_skill["gated"] is False)

    print("\ncase: project bucket is gated")
    p_project = price.price(removed, added, "/some/project/CLAUDE.md")
    check("project bucket outside home", p_project["bucket"] == "project")
    check("project is not gated", p_project["gated"] is False)

report("core-price")
