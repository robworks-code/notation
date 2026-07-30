#!/usr/bin/env python3
"""Mutation tests for the preservation-verification procedure.

These do not test the plugin's markdown - they test that the PROCEDURE the
markdown prescribes actually catches the failures it claims to, by building
each failure and running the checks against it.

The point of each case is the same: the broken run and the healthy run are
indistinguishable to a size check, so if a check here ever stops failing on
the broken input, the procedure has silently lost its teeth.

Run: python3 tests/test_preservation_probe.py
"""

import os
import shutil
import subprocess
import sys
import tempfile

GREP = "/usr/bin/grep"
BLOCK = """### gcloud
- components list is `gcloud components list`
- auth uses `gcloud auth login --no-launch-browser`
- the quota project error string is `getMaxMemoryCharacterCount`
- installed path differs per platform
"""
PROBE = "getMaxMemoryCharacterCount"  # distinctive, from the middle of the block
POINTER = "- gcloud CLI reference: `notes/gcloud.md`\n"

failures = []


def check(name, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
    if not condition:
        failures.append(name)


def hits(needle, path):
    """Literal, line-oriented match via /usr/bin/grep -c -F, as the skill mandates."""
    if not os.path.exists(path):
        return 0
    out = subprocess.run(
        [GREP, "-c", "-F", needle, path], capture_output=True, text=True
    ).stdout.strip()
    return int(out or 0)


def build(tmp, tag):
    src = os.path.join(tmp, f"CLAUDE.{tag}.md")
    dst = os.path.join(tmp, f"gcloud.{tag}.md")
    with open(src, "w") as f:
        f.write("# CLAUDE.md\n\nintro line\n\n" + BLOCK + "\nafter line\n")
    with open(dst, "w") as f:
        f.write("# gcloud notes\n\nexisting unrelated content\n")
    return src, dst


def apply_move(src, dst, *, write_dest=True, remove_src=True, truncate=False):
    """Perform a relocation, optionally breaking one half of it."""
    original = open(src).read()
    if remove_src:
        with open(src, "w") as f:
            f.write(original.replace(BLOCK, POINTER))
    if write_dest:
        text = BLOCK.split("\n")[0] + "\n" if truncate else BLOCK
        with open(dst, "a") as f:
            f.write("\n" + text)


def case_broken_append_shrinks_identically(tmp):
    """The core claim: a failed destination write is invisible to wc -c."""
    print("\ncase: destination append fails, removal succeeds")
    h_src, h_dst = build(tmp, "healthy")
    b_src, b_dst = build(tmp, "broken")
    h_before, b_before = os.path.getsize(h_src), os.path.getsize(b_src)

    apply_move(h_src, h_dst)
    apply_move(b_src, b_dst, write_dest=False)

    h_after, b_after = os.path.getsize(h_src), os.path.getsize(b_src)
    check(
        "broken run shrinks by exactly as much as the healthy run",
        (h_before - h_after) == (b_before - b_after) > 0,
        f"{h_before - h_after} bytes both",
    )
    check("a size-only check calls the BROKEN run a success", b_after < b_before)
    check("probe passes on the healthy run", hits(PROBE, h_dst) >= 1)
    check("probe FAILS on the broken run", hits(PROBE, b_dst) == 0)


def case_inverse_failure(tmp):
    """Append lands, removal does not - passes a destination-only probe."""
    print("\ncase: removal fails, destination append succeeds (inverse failure)")
    src, dst = build(tmp, "inverse")
    apply_move(src, dst, remove_src=False)
    check("destination-side probe PASSES, so it cannot catch this", hits(PROBE, dst) >= 1)
    check(
        "source-side assertion catches it (probe must be gone from source)",
        hits(PROBE, src) != 0,
    )


def case_truncated_write(tmp):
    """Probe in the surviving half passes while the tail is lost."""
    print("\ncase: destination write truncated to the first line")
    src, dst = build(tmp, "trunc")
    dst_before = os.path.getsize(dst)
    removed = len(BLOCK.encode())
    apply_move(src, dst, truncate=True)
    grew = os.path.getsize(dst) - dst_before

    first_line_probe = "### gcloud"
    check(
        "a first-line probe PASSES despite the loss (why the middle is required)",
        hits(first_line_probe, dst) >= 1,
    )
    check("the middle probe catches this truncation", hits(PROBE, dst) == 0)
    check(
        "byte conservation catches it independently of probe placement",
        grew < removed,
        f"destination grew {grew}, needed >= {removed}",
    )


def case_stale_duplicate_precondition(tmp):
    """A probe already present in the destination would false-pass."""
    print("\ncase: probe string already exists in the destination")
    src, dst = build(tmp, "stale")
    with open(dst, "a") as f:
        f.write(f"- old unrelated line mentioning {PROBE}\n")

    pre_src, pre_dst = hits(PROBE, src), hits(PROBE, dst)
    check(
        "precondition REJECTS this probe (present in destination before the move)",
        not (pre_src >= 1 and pre_dst == 0),
    )
    apply_move(src, dst, write_dest=False)  # broken move
    check(
        "and it would indeed have false-passed after a broken move",
        hits(PROBE, dst) >= 1,
    )


def case_shared_destination(tmp):
    """Two blocks into one note: B's probe must not match A's text."""
    print("\ncase: two relocations into the same destination note")
    src, dst = build(tmp, "shared")
    block_b = f"### gcloud extras\n- see also {PROBE} handling\n"
    with open(src, "a") as f:
        f.write("\n" + block_b)

    # B's probe also occurs inside A's block - the precondition must reject it.
    check(
        "precondition REJECTS a probe that appears in another block moving this run",
        PROBE in BLOCK and PROBE in block_b,
        "probe is not unique to its own block",
    )
    apply_move(src, dst)  # only A lands
    check(
        "otherwise B would report verified off A's text",
        hits(PROBE, dst) >= 1,
    )


def main():
    if not os.path.exists(GREP):
        print(f"missing {GREP}", file=sys.stderr)
        return 1
    tmp = tempfile.mkdtemp(prefix="notation-probe-")
    try:
        for case in (
            case_broken_append_shrinks_identically,
            case_inverse_failure,
            case_truncated_write,
            case_stale_duplicate_precondition,
            case_shared_destination,
        ):
            case(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED ({len(failures)}): " + ", ".join(failures))
        return 1
    print("all preservation-procedure mutation checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
