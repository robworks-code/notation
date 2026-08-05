#!/usr/bin/env python3
"""Bucket resolution and file measurement.

Bucket is NOT derivable from whether a path sits under ~/.claude: project
memory lives there and is project-scoped, while notes sit beside it and are
global. That confusion is the reason this lives in one tested function.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from harness import check, report
from notation_core import constants, measure

HOME = os.path.expanduser("~")

print("\ncase: bucket resolution")

check(
    "the global CLAUDE.md is `global`",
    measure.resolve_bucket(os.path.join(HOME, ".claude", "CLAUDE.md")) == "global",
)
check(
    "a topic note is `notes`",
    measure.resolve_bucket(os.path.join(HOME, ".claude", "notes", "railway.md")) == "notes",
)
check(
    "a personal skill is `skill`",
    measure.resolve_bucket(os.path.join(HOME, ".claude", "skills", "x", "SKILL.md")) == "skill",
)
check(
    "a plugin skill is `skill`",
    measure.resolve_bucket(os.path.join(HOME, ".claude", "plugins", "p", "skills", "s", "SKILL.md")) == "skill",
)
check(
    "project memory under ~/.claude is `project`, not global",
    measure.resolve_bucket(os.path.join(HOME, ".claude", "projects", "-a-b", "memory", "m.md")) == "project",
    detail="location does not determine scope; the load condition does",
)
check(
    "a repo CLAUDE.md is `project`",
    measure.resolve_bucket("/Users/x/git/repo/CLAUDE.md") == "project",
)

print("\ncase: only `global` is gated")

check("global is gated", measure.is_gated("global") is True)
check("notes is not gated", measure.is_gated("notes") is False)
check("skill is not gated", measure.is_gated("skill") is False)
check("project is not gated", measure.is_gated("project") is False)

print("\ncase: measurement")

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "CLAUDE.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("# Title\n\n## Index\n\n- a - hook\n- b - hook\n\n## Other\n\nbody\n")
    m = measure.measure(p)
    check("counts characters", m["chars"] == os.path.getsize(p), info="{} chars".format(m["chars"]))
    check("counts lines", m["lines"] == 10, info="{} lines".format(m["lines"]))
    check("counts index-form lines", m["index_lines"] == 2, info="{}".format(m["index_lines"]))
    check(
        "maps sections by heading",
        [s["heading"] for s in m["sections"]] == ["# Title", "## Index", "## Other"],
        detail="got {}".format([s["heading"] for s in m["sections"]]),
    )
    check("section chars sum to file chars", sum(s["chars"] for s in m["sections"]) == m["chars"])

    missing = measure.measure(os.path.join(d, "nope.md"))
    check("a missing file reports exists=False, not chars=0 alone", missing["exists"] is False)
    check("and measures as zero", missing["chars"] == 0)

    bad = os.path.join(d, "bad.md")
    with open(bad, "wb") as fh:
        fh.write(b"ok\n\xff\xfe bad bytes\n")
    raised = False
    try:
        measure.read_text(bad)
    except UnicodeDecodeError:
        raised = True
    check(
        "a non-UTF-8 file raises rather than measuring a partial file",
        raised,
        detail="silently replacing bad bytes yields a confident wrong number",
    )

print("\ncase: target_chars and over_target thresholds")

with tempfile.TemporaryDirectory() as d:
    # Test global-scope target (GLOBAL_TARGET_CHARS)
    small_global = os.path.join(d, ".claude", "CLAUDE.md")
    os.makedirs(os.path.dirname(small_global))
    with open(small_global, "w", encoding="utf-8") as fh:
        fh.write("x" * (constants.GLOBAL_TARGET_CHARS - 100))
    m_small = measure.measure(small_global)
    check(
        "global-scope file has target_chars == GLOBAL_TARGET_CHARS",
        m_small["target_chars"] == constants.GLOBAL_TARGET_CHARS,
        detail="got {}".format(m_small["target_chars"]),
    )
    check(
        "global file under target has over_target == False",
        m_small["over_target"] is False,
        detail="{} chars < {} target".format(m_small["chars"], m_small["target_chars"]),
    )

    large_global = os.path.join(d, ".claude", "CLAUDE2.md")
    with open(large_global, "w", encoding="utf-8") as fh:
        fh.write("x" * (constants.GLOBAL_TARGET_CHARS + 100))
    m_large = measure.measure(large_global)
    check(
        "global file over target has over_target == True",
        m_large["over_target"] is True,
        detail="{} chars > {} target".format(m_large["chars"], m_large["target_chars"]),
    )

    # Test project-scope target (PROJECT_ADVISORY_CHARS)
    small_project = os.path.join(d, "CLAUDE.md")
    with open(small_project, "w", encoding="utf-8") as fh:
        fh.write("x" * (constants.PROJECT_ADVISORY_CHARS - 100))
    m_project_small = measure.measure(small_project)
    check(
        "project-scope file has target_chars == PROJECT_ADVISORY_CHARS",
        m_project_small["target_chars"] == constants.PROJECT_ADVISORY_CHARS,
        detail="got {}".format(m_project_small["target_chars"]),
    )
    check(
        "project file under target has over_target == False",
        m_project_small["over_target"] is False,
        detail="{} chars < {} target".format(m_project_small["chars"], m_project_small["target_chars"]),
    )

    large_project = os.path.join(d, "CLAUDE2.md")
    with open(large_project, "w", encoding="utf-8") as fh:
        fh.write("x" * (constants.PROJECT_ADVISORY_CHARS + 100))
    m_project_large = measure.measure(large_project)
    check(
        "project file over target has over_target == True",
        m_project_large["over_target"] is True,
        detail="{} chars > {} target".format(m_project_large["chars"], m_project_large["target_chars"]),
    )

report("core-measure")
