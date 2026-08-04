---
description: Capture this session's learnings, route each to the right memory tier, and apply every proposal automatically - no interactive picker. Same routing and lean-CLAUDE.md bias as /notation:notate, just without the strategy question. Still prints proposals and backs up CLAUDE.md.
allowed-tools: ["Read", "Edit", "Write", "Glob", "Bash", "AskUserQuestion"]
disable-model-invocation: true
---

# /notation:notate-all

This is `/notation:notate` in auto-apply mode: capture this session's learnings, route each to the tier where it belongs, and apply **all** proposals without the strategy picker.

Read and follow `${CLAUDE_PLUGIN_ROOT}/commands/notate.md` Step 0 and Steps 1-5 exactly (session read + flow shaping, session + project grounding, extracting proposals, routing, dedup, tier-specific formatting). In auto-apply mode Step 0 still applies for **session type, tier focus, and early-exit** - if the read finds nothing worth saving, say so and stop - but it must **never reintroduce a picker**.

**The gate is not optional here.** This command applies every proposal with no
picker, so the gate is the only thing between a bad extraction and the global
file. Run it, and honour a refusal - there is no interactive step that would
otherwise catch it.

Follow `commands/notate.md` Step 2.5's sequence to open the run, then route,
price, and record each proposal - the identical core, the identical commands,
just with nothing standing between the verdict and the write. `$NOTATION` is
`${CLAUDE_PLUGIN_ROOT}`, this plugin's install root.

**`--text-file`, `--removed`, and `--added` all take FILE PATHS, never inline
text** - `route.py`/`price.py` call `os.path.isfile` on each. Write each slice
to a temp file first:

```sh
python3 "$NOTATION/scripts/notation-core.py" open \
  --target ~/.claude/CLAUDE.md --run-id "$RUN" --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

p_file=$(mktemp); printf '%s' "$PROPOSAL_TEXT" > "$p_file"
python3 "$NOTATION/scripts/notation-core.py" route \
  --text-file "$p_file" --target ~/.claude/CLAUDE.md

added_file=$(mktemp); printf '%s' "$DRAFTED_TEXT" > "$added_file"
python3 "$NOTATION/scripts/notation-core.py" price \
  --added "$added_file" --target ~/.claude/CLAUDE.md
```

That `price` call is the pure-addition form - `--removed` omitted, because
this proposal is a NEW entry and nothing is being removed. **`--removed` is
optional for exactly this reason:** an explicit `""` or a nonexistent path is
still refused (a value there means a path was intended and is wrong), so
omitting the flag is the only correct way to price a pure addition. When the
proposal is an UPDATE or relocation that removes an existing slice, write that
slice to its own temp file too and pass both:

```sh
removed_file=$(mktemp); printf '%s' "$REMOVED_TEXT" > "$removed_file"
python3 "$NOTATION/scripts/notation-core.py" price \
  --removed "$removed_file" --added "$added_file" --target ~/.claude/CLAUDE.md
```

Then record whichever price into the run - `$DELTA` and `$BUCKET` come back
out of `price`'s own JSON, not recomputed. `price` alone never touches the
ledger, so skipping `price-record` leaves the proposal invisible to `gate`
below, which is the one check standing in for the picker here:

```sh
python3 "$NOTATION/scripts/notation-core.py" price-record \
  --run-id "$RUN" --delta "$DELTA" --bucket "$BUCKET" --target ~/.claude/CLAUDE.md
```

Act on the `band` the core returns exactly as `commands/notate.md` Step 2.5 describes
(`inline` / `justify` / `must_note`), then immediately before the writes below,
gate the whole run:

```sh
python3 "$NOTATION/scripts/notation-core.py" gate --run-id "$RUN"
```

Exit `0` proceeds. Exit `1` means the run grows the gated global file; report
the `reasons` verbatim and do not write to `~/.claude/CLAUDE.md`. Exit `2` is a
core failure, not a verdict: block the global write, and say the gate could
not run. A project-scoped write proceeds either way, with the warning shown.

After the writes land, close the run:

```sh
python3 "$NOTATION/scripts/notation-core.py" close --run-id "$RUN"
```

A non-zero exit here means the edit did not land as drafted. Report the
`findings` verbatim rather than restating the predicted numbers as if they
happened.

Then run Step 6 in **auto-apply mode**:

- **Print all proposals** using the shared format in `${CLAUDE_PLUGIN_ROOT}/skills/notation-audit/references/output-format.md` (scorecard header, numbered per-tier tables, diffs below keyed by row number) - the same printout Step 6 calls for. If any proposal touches `~/.claude/CLAUDE.md`, include the size ledger.
- **Honor Step 3's budget gate and the core's `gate` verdict.** No picker stands between a proposal and the file here, so the gate is the only thing keeping the every-session file from drifting: if Step 1 measured `~/.claude/CLAUDE.md` at or over the core's global target (`GLOBAL_TARGET_CHARS` in `scripts/notation_core/constants.py`), the global tier is closed by default and borderline learnings route to `notes/` instead. The `gate` subcommand below is the final, authoritative check - it refuses a positive net regardless of what this bullet estimated.
- **Skip every `AskUserQuestion`.** Do not ask the strategy question or per-tier multi-selects. Treat every proposal as approved.
- **Back up every file that will lose content first** - `~/.claude/CLAUDE.md` before any inline rule edit, and equally any note or memory file an `UPDATE` will delete a line from - exactly as Step 6 item 3 specifies, including its **destination rule**: global-scope sources (`~/.claude/CLAUDE.md`, a note) are snapshotted in place, while project-scope sources (`./CLAUDE.md`, a project memory file) go to `~/.claude/notation-backups/<encoded-cwd>/` so nothing lands in the repo working tree. One stamp for the whole run, its value recorded so later Bash calls can substitute it literally. The snapshot must precede the first write, or it preserves the damage rather than the original.
- **Then apply all proposals**, keeping each content change atomic with its index update (a note with its Topical Notes Index line; a memory file with its `MEMORY.md` pointer), picking each removal's probe string before the removal happens.
- **Verify anything that removed content**, exactly as Step 6 item 5 specifies. This matters more here than in the interactive flow: no picker reviewed the deletion, so this probe is the only thing standing between a bad `UPDATE` and a silently lost fact. If a probe misses, restore from the backup and report the loss instead of the size win.
- **Summarize** what was applied, grouped by tier, by absolute path - noting it auto-applied all N proposals. If anything landed in `~/.claude/CLAUDE.md`, **re-measure** it (`close`'s report, cross-checked with `wc -c`) and report `<before> -> <after> chars (target: the core's global target_chars)`, offering a `notation-audit` run if the result is at or over target.
