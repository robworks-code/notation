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
    """-> (tokens, error). Filename plus headings (lines starting with #).

    A note whose bytes cannot be read is NOT silently reduced to its filename.
    Doing that made it count towards notes_searched while its headings could
    never match, so it was invisibly unrankable: present in the denominator,
    absent from every candidate list, and indistinguishable from a note that
    genuinely did not match. The error is returned instead, and rank_notes
    reports it, so a caller can see the file was unreadable rather than
    unmatched.
    """
    name = os.path.basename(path)
    if name.endswith(".md"):
        name = name[:-3]
    text = name.replace("-", " ")
    try:
        body = measure.read_text(path)
    except (IOError, OSError, UnicodeDecodeError) as exc:
        return _tokens(text), "{}: {}".format(type(exc).__name__, exc)
    for line in body.splitlines():
        if line.startswith("#"):
            text += " " + line
    return _tokens(text), None


def rank_notes(text, notes_dir):
    """-> {notes_dir_exists, notes_searched, candidates[], unreadable[]}.

    notes_searched is returned ALWAYS, beside candidates, so an empty list is
    never ambiguous between 'none matched' and 'searched nothing'. unreadable
    is returned on the same terms, so a note that could not be read is never
    mistaken for one that simply did not match.
    """
    full = measure.norm_path(notes_dir)
    if not os.path.isdir(full):
        return {"notes_dir_exists": False, "notes_searched": 0,
                "candidates": [], "unreadable": []}

    wanted = _tokens(text)
    searched = 0
    out = []
    unreadable = []
    for name in sorted(os.listdir(full)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(full, name)
        searched += 1
        tokens, error = _note_tokens(path)
        if error:
            unreadable.append({"path": path, "error": error})
        matched = sorted(wanted & tokens)
        if matched:
            out.append({"path": path, "score": len(matched), "matched_tokens": matched})

    out.sort(key=lambda c: (-c["score"], c["path"]))
    return {"notes_dir_exists": True, "notes_searched": searched,
            "candidates": out, "unreadable": unreadable}


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
        "unreadable": ranked["unreadable"],
    }
