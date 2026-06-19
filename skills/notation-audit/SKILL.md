---
name: notation-audit
description: Audit and rebalance Claude Code memory notation across CLAUDE.md, ~/.claude/notes/, and per-project MEMORY.md. Use when the user asks to audit notes, check CLAUDE.md for bloat, find stale or orphaned notes, rebalance memory tiers, or mentions "notation health" or "notation maintenance".
---

# Notation Audit

Inspect the health of the user's Claude Code memory across all tiers, report problems, then offer targeted fixes. This is the diagnostic counterpart to `/notation:notate` (which captures new learnings); use it to clean up what is already there.

## What the tiers are

- **Global rules** - `~/.claude/CLAUDE.md`: lean, loads every session. Only high-frequency, cross-project rules belong inline.
- **Topical notes** - `~/.claude/notes/*.md`: situational, loaded on demand, each registered by a line in the "Topical Notes Index" at the bottom of CLAUDE.md.
- **Project memory** - `~/.claude/projects/<encoded-cwd>/memory/`: one fact per frontmatter file, indexed by `MEMORY.md`.
- **Project docs / CLAUDE.md** - `./.claude/docs/`, `./CLAUDE.md`: project-tracked guides and team conventions.

## How to run an audit

1. Read `~/.claude/CLAUDE.md` and `Glob` `~/.claude/notes/*.md`. For the current project, locate the memory dir via `ls -d ~/.claude/projects/*/memory 2>/dev/null` and read its `MEMORY.md`.
2. Walk the checklist in `references/audit-checklist.md` and collect findings.
3. Report findings using the shared format in `references/output-format.md`: a scorecard header (`Audited: ... - <x> move - <y> fix - <z> tidy`), then one numbered table per severity group (move / fix / tidy) with columns `# - title - severity - problem`, each row referencing a file by absolute path.
4. Offer to apply fixes. Apply only what the user approves. Before editing `~/.claude/CLAUDE.md`, back it up: `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak.$(date +%Y%m%d-%H%M%S)`.

## What to look for (summary)

- **CLAUDE.md bloat**: inline entries that are tool/platform/API-specific and belong in `notes/`. These are the highest-value moves - they shrink the every-session prompt.
- **Orphaned index lines**: a Topical Notes Index entry whose `notes/<topic>.md` file does not exist, or a note file with no index line.
- **Oversized notes**: a single note that has grown large enough to split by sub-topic.
- **Memory without a pointer**: a frontmatter memory file with no matching line in `MEMORY.md` (or a `MEMORY.md` line pointing at a missing file).
- **Cross-tier duplication**: the same fact living in two tiers.
- **Backup clutter**: stale `~/.claude/CLAUDE.md.bak.*` snapshots the user may want to prune.

Full detail and the routing rubric used to decide where a stray entry should move: `references/audit-checklist.md` and `references/routing-rubric.md`.

## Style
- Use plain hyphens (`-`) only. No em-dashes or en-dashes.
- Never edit `~/.claude/settings.json`.
- Be concise; reference files by absolute path.
