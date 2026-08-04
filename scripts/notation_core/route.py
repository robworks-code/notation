"""Size banding and existing-note candidate ranking.

Ranking is deliberately simple and explainable: the session has to be able to
state why nothing fit before it is allowed to mint a new note.
"""

import os
import re

from . import constants, measure

TOKEN = re.compile(r"[a-z0-9]+")
STOP = frozenset([
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "to", "of", "in", "on", "at", "for", "with", "from", "by", "it", "its",
    "this", "that", "not", "must", "can", "will", "when", "then", "than",
])


def _tokens(text):
    return set(t for t in TOKEN.findall(text.lower()) if t not in STOP and len(t) > 2)


def band(text):
    """-> 'inline' | 'justify' | 'must_note' for a proposed addition."""
    n = len(text)
    if n <= constants.INLINE_MAX:
        return "inline"
    if n <= constants.JUSTIFY_MAX:
        return "justify"
    return "must_note"


def _note_tokens(path):
    """Filename plus headings plus first line of each section."""
    name = os.path.basename(path)
    if name.endswith(".md"):
        name = name[:-3]
    text = name.replace("-", " ")
    try:
        body = measure.read_text(path)
    except (IOError, OSError, UnicodeDecodeError):
        return _tokens(text)
    for line in body.splitlines():
        if line.startswith("#"):
            text += " " + line
    return _tokens(text)


def rank_notes(text, notes_dir):
    """-> {notes_dir_exists, notes_searched, candidates[]}.

    notes_searched is returned ALWAYS, beside candidates, so an empty list is
    never ambiguous between 'none matched' and 'searched nothing'.
    """
    full = os.path.abspath(os.path.expanduser(notes_dir))
    if not os.path.isdir(full):
        return {"notes_dir_exists": False, "notes_searched": 0, "candidates": []}

    wanted = _tokens(text)
    searched = 0
    out = []
    for name in sorted(os.listdir(full)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(full, name)
        searched += 1
        matched = sorted(wanted & _note_tokens(path))
        if matched:
            out.append({"path": path, "score": len(matched), "matched_tokens": matched})

    out.sort(key=lambda c: (-c["score"], c["path"]))
    return {"notes_dir_exists": True, "notes_searched": searched, "candidates": out}


def route(text, target, notes_dir):
    """-> the full routing verdict for one proposed addition."""
    b = band(text)
    ranked = rank_notes(text, notes_dir)
    return {
        "band": b,
        "requires_reason": b == "justify",
        "bucket": measure.resolve_bucket(target),
        "notes_dir_exists": ranked["notes_dir_exists"],
        "notes_searched": ranked["notes_searched"],
        "candidates": ranked["candidates"],
    }
