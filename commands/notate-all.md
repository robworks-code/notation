---
description: Capture this session's learnings, route each to the right memory tier, and apply every proposal automatically - no interactive picker. Same routing and lean-CLAUDE.md bias as /notation:notate, just without the strategy question. Still prints proposals and backs up CLAUDE.md.
allowed-tools: ["Read", "Edit", "Write", "Glob", "Bash", "AskUserQuestion"]
disable-model-invocation: true
---

# /notation:notate-all

This is `/notation:notate` in auto-apply mode: capture this session's learnings, route each to the tier where it belongs, and apply **all** proposals without the strategy picker.

Read and follow `${CLAUDE_PLUGIN_ROOT}/commands/notate.md` Step 0 and Steps 1-5 exactly (session read + flow shaping, session + project grounding, extracting proposals, routing, dedup, tier-specific formatting). In auto-apply mode Step 0 still applies for **session type, tier focus, and early-exit** - if the read finds nothing worth saving, say so and stop - but it must **never reintroduce a picker**. Then run Step 6 in **auto-apply mode**:

- **Print all proposals** using the shared format in `${CLAUDE_PLUGIN_ROOT}/skills/notation-audit/references/output-format.md` (scorecard header, numbered per-tier tables, diffs below keyed by row number) - the same printout Step 6 calls for. If any proposal touches `~/.claude/CLAUDE.md`, include the size ledger.
- **Honor Step 3's budget gate.** No picker stands between a proposal and the file here, so the gate is the only thing keeping the every-session file from drifting: if Step 1 measured `~/.claude/CLAUDE.md` at or over 40,000 chars, the global tier is closed by default and borderline learnings route to `notes/` instead.
- **Skip every `AskUserQuestion`.** Do not ask the strategy question or per-tier multi-selects. Treat every proposal as approved.
- **Back up every file that will lose content first** - `~/.claude/CLAUDE.md` before any inline rule edit, and equally any note or memory file an `UPDATE` will delete a line from - exactly as Step 6 item 3 specifies, including its **destination rule**: global-scope sources (`~/.claude/CLAUDE.md`, a note) are snapshotted in place, while project-scope sources (`./CLAUDE.md`, a project memory file) go to `~/.claude/notation-backups/<encoded-cwd>/` so nothing lands in the repo working tree. One stamp for the whole run, its value recorded so later Bash calls can substitute it literally. The snapshot must precede the first write, or it preserves the damage rather than the original.
- **Then apply all proposals**, keeping each content change atomic with its index update (a note with its Topical Notes Index line; a memory file with its `MEMORY.md` pointer), picking each removal's probe string before the removal happens.
- **Verify anything that removed content**, exactly as Step 6 item 5 specifies. This matters more here than in the interactive flow: no picker reviewed the deletion, so this probe is the only thing standing between a bad `UPDATE` and a silently lost fact. If a probe misses, restore from the backup and report the loss instead of the size win.
- **Summarize** what was applied, grouped by tier, by absolute path - noting it auto-applied all N proposals. If anything landed in `~/.claude/CLAUDE.md`, **re-measure** it (`wc -c`) and report `<before> -> <after> chars (target 40,000)`, offering a `notation-audit` run if the result is at or over target.
