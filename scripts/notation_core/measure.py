"""Bucket resolution and file measurement - the one place size is computed."""

import os
import re

from . import constants

INDEX_LINE = re.compile(r"^- \S")
HEADING = re.compile(r"^#+ ")


def norm_path(path):
    """-> the one canonical spelling of a path. Every reader and writer uses it.

    ~ is expanded, the result is made absolute against the cwd, and normpath
    collapses `.` and `..` lexically. It deliberately does NOT follow symlinks:
    a file the user named through a symlink is still the file the user named,
    and scope has to follow that naming (see _home_rels).

    Keying by anything else is how a target written by one subcommand fails to
    match the same target read by another - '~/.claude/CLAUDE.md' quoted so the
    shell never expanded it, or a relative path, are the same file and must
    produce the same key.
    """
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))


def _homes():
    """-> candidate absolute spellings of the home directory, no duplicates."""
    raw = os.path.expanduser("~")
    out = []
    for h in (os.path.normpath(os.path.abspath(raw)), os.path.realpath(raw)):
        h = os.path.normpath(h)
        if h not in out:
            out.append(h)
    return out


def _home_rels(path):
    """-> every plausible ~-relative spelling of the path, best first.

    The path the caller NAMED comes first and decides scope. A
    ~/.claude/CLAUDE.md that is a symlink into a dotfiles repo is still the
    global file, so realpath must not be what answers this question - doing so
    silently demoted the gated file to bucket 'project' and disarmed the gate
    entirely.

    normpath has already collapsed any `..` before the comparison, so a path
    that climbs out of ~ cannot masquerade as a path inside it.

    The realpath spelling is appended only as a fallback, for the reverse case:
    a path reached THROUGH a symlinked parent (macOS /var -> /private/var, or
    a home directory that is itself a link). resolve_bucket consults it only
    when it would tighten the bucket, never to loosen one.
    """
    named = norm_path(path)
    spellings = [named]
    real = os.path.realpath(named)
    if real != named:
        spellings.append(real)

    rels = []
    for full in spellings:
        for home in _homes():
            if full == home:
                rel = ""
            elif full.startswith(home + os.sep):
                rel = full[len(home) + 1:].replace(os.sep, "/")
            else:
                continue
            if rel not in rels:
                rels.append(rel)
    return rels


def _bucket_for_rel(rel):
    """-> the bucket one ~-relative path spelling implies.

    Location does not determine scope. Project memory lives under
    ~/.claude/projects/ and is project-scoped; notes sit beside it and are
    global. The five prefixes are mutually exclusive, so the order they are
    written in has no effect on the result - permuting them changes nothing.
    What is load-bearing is that .claude/projects/ is tested at all, since it
    is the one under-.claude location that is NOT global-scoped.
    """
    if rel.startswith(".claude/projects/"):
        return "project"
    if rel == ".claude/CLAUDE.md":
        return "global"
    if rel.startswith(".claude/notes/"):
        return "notes"
    if rel.startswith(".claude/skills/") or rel.startswith(".claude/plugins/"):
        return "skill"
    return "project"


def resolve_bucket(path):
    """-> 'global' | 'notes' | 'skill' | 'project'.

    Decided from the path the caller named (see _home_rels). A symlinked
    target keeps the scope of the name, not of the link's destination.

    When a fallback spelling disagrees with the named one, 'global' wins: the
    gated file is the only bucket whose misresolution costs anything, and
    over-gating is recoverable where under-gating is silent.
    """
    rels = _home_rels(path)
    if not rels:
        return "project"
    buckets = [_bucket_for_rel(r) for r in rels]
    if "global" in buckets:
        return "global"
    return buckets[0]


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
    full = norm_path(path)
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
