#!/usr/bin/env python3
"""Pin commands/notate.md and commands/notate-all.md to the core's real CLI.

Task 9 wired both capture command docs to invoke scripts/notation-core.py.
Nothing stops the docs from drifting from the shipped CLI afterward - a
renamed subcommand, a dropped flag, or a reintroduced hardcoded threshold
would leave the docs describing a tool that no longer exists, silently. This
file reads the actual argparse definition (the CLI's own source of truth) and
the actual constants module, then asserts the docs stay honest about both.

Run: python3 tests/test_command_doc_drift.py
"""

import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import check, report

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTATE = os.path.join(REPO, "commands", "notate.md")
NOTATE_ALL = os.path.join(REPO, "commands", "notate-all.md")
CLI = os.path.join(REPO, "scripts", "notation_core", "cli.py")
CONSTANTS = os.path.join(REPO, "scripts", "notation_core", "constants.py")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Import the real package so cli.py's relative imports (`from . import ...`)
# resolve, rather than exec'ing cli.py in isolation.
sys.path.insert(0, os.path.join(REPO, "scripts"))
cli = load_module("notation_core.cli", CLI)
constants = load_module("notation_core.constants", CONSTANTS)

parser = cli._parser()
subcommands = sorted(
    a.choices.keys() for a in parser._subparsers._group_actions
)[0]

notate_text = read(NOTATE)
notate_all_text = read(NOTATE_ALL)
both = notate_text + "\n" + notate_all_text

print("\ncase: every real subcommand is named in at least one command doc")
for cmd in subcommands:
    check(
        "'{}' appears in a doc".format(cmd),
        re.search(r"\b{}\b".format(re.escape(cmd)), both) is not None,
    )

print("\ncase: notate.md's Step 2.5 and notate-all.md invoke the actual entry point")
for path, text in ((NOTATE, notate_text), (NOTATE_ALL, notate_all_text)):
    check(
        "{} references scripts/notation-core.py".format(os.path.basename(path)),
        "notation-core.py" in text,
    )

print("\ncase: both docs run open, route, price, price-record, gate, and close - not a subset")
for path, text in ((NOTATE, notate_text), (NOTATE_ALL, notate_all_text)):
    for cmd in ("open", "route", "price", "price-record", "gate", "close"):
        check(
            "{} runs '{}'".format(os.path.basename(path), cmd),
            re.search(r"notation-core\.py\W+{}\b".format(cmd), text) is not None,
        )

print("\ncase: gate's required flag is documented")
gate_parser = parser._subparsers._group_actions[0].choices["gate"]
gate_flags = {a.option_strings[0] for a in gate_parser._actions if a.option_strings} - {"-h"}
for flag in gate_flags:
    check(
        "gate's {} is shown in notate.md".format(flag),
        flag in notate_text,
    )

print("\ncase: no command doc restates a routing band or size-target number")
# The bands and file-size targets are constants.py's alone (see its own
# docstring). A literal 200 / 600 / 40000 / 20000 in these docs means a
# threshold got typed twice, and the two copies can now disagree silently.
THRESHOLD = re.compile(r"\b(200|600|40,?000|20,?000)\b")
for path, text in ((NOTATE, notate_text), (NOTATE_ALL, notate_all_text)):
    hits = THRESHOLD.findall(text)
    check(
        "{} has no literal threshold number".format(os.path.basename(path)),
        not hits,
        detail="found {}".format(hits),
    )

print("\ncase: the constants module still defines the values the docs point at")
# Not a numeric pin (that would reintroduce the drift this test guards
# against) - just proof the names the docs cite still exist in constants.py,
# so a rename there is caught here instead of silently orphaning a doc
# reference. INLINE_MAX/JUSTIFY_MAX are deliberately NOT named in the docs
# (the docs describe their effect - the 'inline'/'justify'/'must_note' bands
# route.py already returns - rather than the symbol names), so only the
# size-target constants, which the docs do cite by name, are checked here.
for name in ("GLOBAL_TARGET_CHARS", "PROJECT_SILENT_CHARS", "PROJECT_ADVISORY_CHARS"):
    check(
        "constants.py defines {}".format(name),
        hasattr(constants, name),
    )
    check(
        "{} is named in a command doc".format(name),
        name in both,
    )

print("\ncase: both docs describe all three routing bands by name")
for band_name in ("inline", "justify", "must_note"):
    check(
        "'{}' band is named in a command doc".format(band_name),
        "`{}`".format(band_name) in both,
    )

print("\ncase: price's actual flags are named in both docs' price invocations")
# route/price/price take FILE PATHS (os.path.isfile in the core), and --removed
# is optional there - a session that reads only the flag names, not the
# surrounding prose, must still see the real flag set. Read the flags off the
# live argparse definition rather than a hand-kept list, so a flag rename is
# caught here too.
price_parser = parser._subparsers._group_actions[0].choices["price"]
price_flags = {a.option_strings[0] for a in price_parser._actions
               if a.option_strings} - {"-h"}
for path, text in ((NOTATE, notate_text), (NOTATE_ALL, notate_all_text)):
    for flag in price_flags:
        check(
            "{}'s price invocation shows {}".format(os.path.basename(path), flag),
            flag in text,
        )

print("\ncase: both docs state that route/price take file paths, not inline text")
# This is the defect a live reviewer hit: --removed/--added take paths
# (os.path.isfile), but nothing near them said so, so the natural reading -
# Step 2 calls this a 'diff' - was to pass literal text and get a ValueError.
for path, text in ((NOTATE, notate_text), (NOTATE_ALL, notate_all_text)):
    check(
        "{} states --text-file/--removed/--added take file paths".format(
            os.path.basename(path)),
        "FILE PATHS" in text,
    )
    check(
        "{} shows how to produce those paths (mktemp)".format(os.path.basename(path)),
        "mktemp" in text,
    )

print("\ncase: both docs show the pure-addition form (--removed omitted)")
# price's --removed is optional specifically so a NEW proposal - the common
# case - has a legal invocation. A doc that only ever shows --removed being
# passed leaves that path undiscoverable.
PURE_ADDITION = re.compile(
    r'notation-core\.py"\s+price\s+\\\s*\n\s+--added\b'
)
for path, text in ((NOTATE, notate_text), (NOTATE_ALL, notate_all_text)):
    check(
        "{} shows a price call with --removed omitted".format(os.path.basename(path)),
        PURE_ADDITION.search(text) is not None,
    )

report("command-doc-drift")
