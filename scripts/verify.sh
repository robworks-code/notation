#!/bin/sh
# The whole gate for this repo, in one command. CI, if it ever exists, calls this.
#
#   ./scripts/verify.sh
#
# Checks: manifest validity, ASCII-only content, resolvable cross-references
# between skill files, scope resolution, the backup-listing recipe, and the
# preservation-procedure mutation tests.
set -eu

cd "$(dirname "$0")/.."
fail=0

step() { printf '\n== %s ==\n' "$1"; }
bad() { printf 'FAIL: %s\n' "$1"; fail=1; }

step "manifest"
if command -v claude >/dev/null 2>&1; then
  claude plugin validate . || bad "plugin validate"
else
  printf 'claude CLI not found - checking JSON only\n'
fi
python3 -c "import json; d=json.load(open('.claude-plugin/plugin.json')); print('version', d['version'])" \
  || bad "plugin.json does not parse"

step "ASCII only"
python3 - <<'PY' || fail=1
import subprocess, sys
files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
bad = []
for f in files:
    try:
        text = open(f, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    for i, line in enumerate(text.splitlines(), 1):
        for ch in line:
            if ord(ch) > 127:
                bad.append(f"{f}:{i}: U+{ord(ch):04X} {ch!r}")
print("\n".join(bad) if bad else "clean")
sys.exit(1 if bad else 0)
PY

step "cross-references"
python3 - <<'PY' || fail=1
import glob, os, re, sys
# Files the skill points at by bare name. Anything named `<slug>.md` in backticks
# inside a skill/command file must exist, except names that are examples of a
# USER's own note file rather than a reference shipped here.
EXAMPLES = {"external-apis.md", "gcloud.md", "railway.md", "supabase.md", "pytest.md"}
base = "skills/notation-audit"
missing = []
for path in glob.glob(base + "/**/*.md", recursive=True) + glob.glob("commands/*.md"):
    for name in re.findall(r"`([a-z0-9-]+\.md)`", open(path).read()):
        if name in EXAMPLES:
            continue
        if not any(os.path.exists(c) for c in
                   (os.path.join(base, "references", name), os.path.join(base, name), name)):
            missing.append(f"{path} -> {name}")
print("\n".join(missing) if missing else "all resolve")
sys.exit(1 if missing else 0)
PY

step "scope-resolution tests"
python3 tests/test_scope_resolution.py || bad "scope-resolution tests"

step "rule-precedence tests"
python3 tests/test_rule_precedence.py || bad "rule-precedence tests"

step "backup-lifecycle tests"
python3 tests/test_backup_lifecycle.py || bad "backup-lifecycle tests"

step "preservation-procedure mutation tests"
python3 tests/test_preservation_probe.py || bad "preservation mutation tests"

step "detection-coverage tests"
python3 tests/test_detection_coverage.py || bad "detection-coverage tests"

step "command-doc-drift tests"
python3 tests/test_command_doc_drift.py || bad "command-doc-drift tests"

step "notation_core tests"
python3 tests/test_core_measure.py        || bad "core-measure tests"
python3 tests/test_core_route.py          || bad "core-route tests"
python3 tests/test_core_price.py          || bad "core-price tests"
python3 tests/test_core_ledger.py         || bad "core-ledger tests"
python3 tests/test_core_ledger_errors.py  || bad "core-ledger-errors tests"
python3 tests/test_core_gate.py           || bad "core-gate tests"
python3 tests/test_core_close.py          || bad "core-close tests"
python3 tests/test_core_cli.py            || bad "core-cli tests"
python3 tests/test_core_roundtrip.py      || bad "core-roundtrip tests"
python3 tests/test_core_seams.py          || bad "core-seams tests"

printf '\n'
if [ "$fail" -ne 0 ]; then
  printf 'VERIFY FAILED\n'
  exit 1
fi
printf 'VERIFY PASSED\n'
