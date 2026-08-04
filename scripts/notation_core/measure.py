"""Bucket resolution and file measurement - the one place size is computed."""

import os
import re

from . import constants

INDEX_LINE = re.compile(r"^- \S")
HEADING = re.compile(r"^#+ ")


def _home_rel(path):
    """-> path relative to ~, using forward slashes, or None if outside ~."""
    home = os.path.realpath(os.path.expanduser("~"))
    full = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    if full == home:
        return ""
    prefix = home + os.sep
    if not full.startswith(prefix):
        return None
    return full[len(prefix):].replace(os.sep, "/")


def resolve_bucket(path):
    """-> 'global' | 'notes' | 'skill' | 'project'.

    Location does not determine scope. Project memory lives under
    ~/.claude/projects/ and is project-scoped; notes sit beside it and are
    global. Order matters: the project-memory test runs before the
    under-.claude tests.
    """
    rel = _home_rel(path)
    if rel is None:
        return "project"
    if rel.startswith(".claude/projects/"):
        return "project"
    if rel == ".claude/CLAUDE.md":
        return "global"
    if rel.startswith(".claude/notes/"):
        return "notes"
    if rel.startswith(".claude/skills/") or rel.startswith(".claude/plugins/"):
        return "skill"
    return "project"


def is_gated(bucket):
    """Only the every-session global file feeds the no-growth gate."""
    return bucket == "global"


def read_text(path):
    """Read UTF-8 strictly. Bad bytes raise rather than being replaced."""
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def _target_chars(bucket):
    if bucket == "global":
        return constants.GLOBAL_TARGET_CHARS
    if bucket == "project":
        return constants.PROJECT_ADVISORY_CHARS
    return None


def measure(path):
    """-> dict describing one file. A missing file is exists=False, not an error."""
    bucket = resolve_bucket(path)
    target = _target_chars(bucket)
    full = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(full):
        return {
            "path": full, "exists": False, "chars": 0, "lines": 0,
            "index_lines": 0, "sections": [], "bucket": bucket,
            "gated": is_gated(bucket), "target_chars": target, "over_target": False,
        }

    text = read_text(full)
    lines = text.splitlines(True)
    sections = []
    heading = None
    size = 0
    for line in lines:
        if HEADING.match(line):
            if heading is not None:
                sections.append({"heading": heading, "chars": size})
            heading = line.strip()
            size = 0
        size += len(line)
    if heading is not None:
        sections.append({"heading": heading, "chars": size})
    elif lines:
        sections.append({"heading": "(no heading)", "chars": sum(len(x) for x in lines)})

    chars = len(text)
    return {
        "path": full,
        "exists": True,
        "chars": chars,
        "lines": len(lines),
        "index_lines": sum(1 for x in lines if INDEX_LINE.match(x)),
        "sections": sections,
        "bucket": bucket,
        "gated": is_gated(bucket),
        "target_chars": target,
        "over_target": bool(target and chars > target),
    }
