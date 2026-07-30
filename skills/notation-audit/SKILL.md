---
name: notation-audit
description: Audit and rebalance Claude Code memory notation across CLAUDE.md, ~/.claude/notes/, and per-project MEMORY.md. Use when the user asks to audit notes, check CLAUDE.md for bloat, find stale or orphaned notes, rebalance memory tiers, shrink an oversized CLAUDE.md back under the size warning threshold, or mentions "notation health" or "notation maintenance".
---

# Notation Audit

Inspect the health of the user's Claude Code memory across all tiers, report problems, then offer targeted fixes. This is the diagnostic counterpart to `/notation:notate` (which captures new learnings); use it to clean up what is already there.

## What the tiers are

- **Global rules** - `~/.claude/CLAUDE.md`: lean, loads every session. Only high-frequency, cross-project rules belong inline.
- **Topical notes** - `~/.claude/notes/*.md`: situational, loaded on demand, each registered by a line in the "Topical Notes Index" at the bottom of CLAUDE.md.
- **Project memory** - `~/.claude/projects/<encoded-cwd>/memory/`: one fact per frontmatter file, indexed by `MEMORY.md`.
- **Project docs / CLAUDE.md** - `./.claude/docs/`, `./CLAUDE.md`: project-tracked guides and team conventions.

## How to run an audit

1. **Measure first.** `wc -c ~/.claude/CLAUDE.md` (and `wc -c ./CLAUDE.md 2>/dev/null` - test that the file *exists*, not that git tracks it; it is commonly gitignored yet still loaded) and compare against the budgets in `references/size-budget.md`. Then read `~/.claude/CLAUDE.md`, `Glob` `~/.claude/notes/*.md`, and for the current project locate the memory dir via `ls -d ~/.claude/projects/*/memory 2>/dev/null` and read its `MEMORY.md`.
2. Walk the checklist in `references/audit-checklist.md` and collect findings. If the measured size is over target, keep proposing relocations until the projected size lands under it (or until nothing is left that can move without losing value).
3. Report findings using the shared format in `references/output-format.md`: a scorecard header (`Audited: ... - <x> move - <y> fix - <z> tidy`) plus the **size ledger** (before -> projected -> target), then one numbered table per severity group (move / fix / tidy) with columns `# - title - severity - problem - delta`, each row referencing a file by absolute path and carrying its signed character delta against the file that row touches. Global-file and project-file deltas total separately and are never pooled; only the global total feeds the no-growth gate.
4. Offer to apply fixes. Apply only what the user approves. Before editing `~/.claude/CLAUDE.md`, back it up: `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak.$(date +%Y%m%d-%H%M%S)`.
5. **Re-measure after applying** (`wc -c ~/.claude/CLAUDE.md`) and report before -> after -> target with real numbers. If the run ended net-positive, or still over target, say so and offer the next round.

**Two files are called CLAUDE.md; they get opposite treatment.** `~/.claude/CLAUDE.md` (global) loads into every prompt of every session and is **strictly** budgeted. A repo's own `./CLAUDE.md` loads only in that repo, so it gets **headroom**: silent under 20,000 chars, one advisory line up to 40,000, and only past that a real (still advisory) finding. There is no no-growth rule for a project file, and its detail relocates to project-local homes (`./.claude/docs/`, the repo's docs, project memory) - never into the global `~/.claude/notes/`. Strict enforcement on a project file happens only when the user asks or a project memory records that preference. Full rules: `references/size-budget.md`.

**The global file must shrink, never grow.** `~/.claude/CLAUDE.md` loads into every prompt, so an audit that leaves it larger than it found it has failed - even if every finding was correct. The applied net character delta must be `<= 0` always, and when the file is over the 40,000-char target the audit must propose enough relocation to get under it. Additive findings (a new index line, a restored description) are legitimate but must be **counted in the ledger and offset** by moves in the same run. Full budget, tactics, and ledger format: `references/size-budget.md`.

**Preservation first - shrink by relocating, never by trimming.** The budget above is satisfied by **moving** facts into `~/.claude/notes/` and leaving a one-line pointer, not by deleting them. Never propose dropping a still-true line to save space. The only safe deletions are a redundant cross-tier copy (the fact survives elsewhere) or a line that is factually wrong or contradicted by newer notation, and those must be named explicitly. If the budget can only be met by destroying a fact, **miss the budget and say why** - losing a hard-won line is worse than a slightly long file. Full rule: `references/routing-rubric.md` > "Preservation".

## What to look for (summary)

- **Over the size budget**: `~/.claude/CLAUDE.md` above ~40,000 chars. This is the finding that sets the run's goal - everything else is scored against it. (A project `./CLAUDE.md` is scored separately and far more loosely - most never get mentioned.)
- **CLAUDE.md bloat**: inline entries that are tool/platform/API-specific and belong in `notes/`. These are the highest-value **moves** (relocate every fact, do not trim) - they shrink the every-session prompt without losing anything.
- **Bloated index hooks**: Topical Notes Index lines that teach instead of route. In a mature setup the index can be a third of the whole file; capping hooks at ~100 chars is often the second-biggest lever.
- **Orphaned index lines**: a Topical Notes Index entry whose `notes/<topic>.md` file does not exist, or a note file with no index line.
- **Oversized notes**: a single note that has grown large enough to split by sub-topic.
- **Memory without a pointer**: a frontmatter memory file with no matching line in `MEMORY.md` (or a `MEMORY.md` line pointing at a missing file).
- **Cross-tier duplication**: the same fact living in two tiers - keep the more specific copy, drop the redundant one.
- **Missing recency dates**: new-style notes entries or memory files lacking a date; nudge new additions toward `(YYYY-MM-DD)` / `metadata.updated`.
- **Backup clutter**: stale `~/.claude/CLAUDE.md.bak.*` snapshots the user may want to prune (keep the most recent one or two - they are the preservation safety net).

Full detail and the routing rubric used to decide where a stray entry should move: `references/audit-checklist.md`, `references/routing-rubric.md`, and `references/size-budget.md`.

## Style
- Use plain hyphens (`-`) only. No em-dashes or en-dashes.
- Never edit `~/.claude/settings.json`.
- Be concise; reference files by absolute path.
