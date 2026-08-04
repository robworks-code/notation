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
- **Skills** - `~/.claude/skills/<name>/SKILL.md` and plugin skills: procedural how-to, loaded on demand by name. A skill is BOTH a valid relocation destination and a duplication counterparty. Do not treat it as out of scope because this plugin ships as one: an inline CLAUDE.md section that names a skill is the highest-confidence move in the file, and check 5 must compare against skills the same way it compares against notes.

## How to run an audit

1. **Measure first.** `wc -c ~/.claude/CLAUDE.md` (and `wc -c ./CLAUDE.md 2>/dev/null` - test that the file *exists*, not that git tracks it; it is commonly gitignored yet still loaded) and compare against the budgets in `references/size-budget.md`. Then read `~/.claude/CLAUDE.md`, `Glob` `~/.claude/notes/*.md`, and for the current project resolve **this** project's memory dir by exact path - inline the encoding in the same Bash call, `enc=$(printf '%s' "$PWD" | sed 's#[/.]#-#g'); ls -d "$HOME/.claude/projects/$enc/memory"`, never a `*` glob and never a helper defined in an earlier call (shell state does not persist between them) - and read its `MEMORY.md`. The encoding replaces `/` **and** `.` with `-`; full rule and the edge cases (dir absent, additional working directories) in `references/scope-resolution.md`.
2. Walk the checklist in `references/audit-checklist.md` and collect findings. If the measured size is over target, keep proposing relocations until the projected size lands under it (or until nothing is left that can move without losing value).
3. Report findings using the shared format in `references/output-format.md`: a scorecard header (`Audited: ... - <x> move - <y> fix - <z> tidy`) plus the **size ledger** (before -> projected -> target), then one numbered table per severity group (move / fix / tidy) with columns `# - title - severity - problem - delta`, each row referencing a file by absolute path and carrying its signed character delta against the file that row touches. Deltas total separately per bucket and are never pooled - `global` (`~/.claude/CLAUDE.md`), `notes` (`~/.claude/notes/`), `project` (`./CLAUDE.md`, `./.claude/docs/`, project memory), each with its own ledger line; only the `global` total feeds the no-growth gate.
4. Offer to apply fixes. Apply only what the user approves. **Before the first write, back up every file the run will remove content from** - `~/.claude/CLAUDE.md`, plus any note being consolidated away, `./CLAUDE.md` on a strict run, and any **project memory file** check 9 is moving a fact out of - using one timestamp for the whole set. Global-scope sources are backed up in place; project-scope sources go to `~/.claude/notation-backups/<encoded-cwd>/` so nothing lands in the repo working tree (`references/verify-after-apply.md`). While the source text is still in front of you, pick 1-2 distinctive probe strings per relocation and assert their preconditions (`references/verify-after-apply.md`).
5. **Verify after applying, in this order:** confirm each relocated block's destination **grew by at least the bytes that left**, confirm each probe now hits its destination and is **gone from the source**, then re-measure (`wc -c`) and report before -> after -> target with real numbers. If a check fails, restore just that relocation from its snapshot and report the loss; do not report the size win. If the run ended net-positive, or still over target, say so and offer the next round. Full procedure: `references/verify-after-apply.md`.

**Two files are called CLAUDE.md; they get opposite treatment.** `~/.claude/CLAUDE.md` (global) loads into every prompt of every session and is **strictly** budgeted. A repo's own `./CLAUDE.md` loads only in that repo, so it gets **headroom**: silent under 20,000 chars, one advisory line up to 40,000, and only past that a real (still advisory) finding. There is no no-growth rule for a project file, and its detail relocates to project-local homes (`./.claude/docs/`, the repo's docs, project memory) - never into the global `~/.claude/notes/`. Strict enforcement on a project file happens only when the user asks or a project memory records that preference. Full rules: `references/size-budget.md`.

**The global file must shrink, never grow.** `~/.claude/CLAUDE.md` loads into every prompt, so an audit that leaves it larger than it found it has failed - even if every finding was correct. The applied net character delta must be `<= 0` always, and when the file is over the 40,000-char target the audit must propose enough relocation to get under it. Additive findings (a new index line, a restored description) are legitimate but must be **counted in the ledger and offset** by moves in the same run. Full budget, tactics, and ledger format: `references/size-budget.md`.

**Preservation first - shrink by relocating, never by trimming.** The budget above is satisfied by **moving** facts into `~/.claude/notes/` and leaving a one-line pointer, not by deleting them. Never propose dropping a still-true line to save space. The only safe deletions are a redundant cross-tier copy (the fact survives elsewhere) or a line that is factually wrong or contradicted by newer notation, and those must be named explicitly. If the budget can only be met by destroying a fact, **miss the budget and say why** - losing a hard-won line is worse than a slightly long file. Full rule: `references/routing-rubric.md` > "Preservation".

## What to look for (summary)

- **Over the size budget**: `~/.claude/CLAUDE.md` above ~40,000 chars. This is the finding that sets the run's goal - everything else is scored against it. (A project `./CLAUDE.md` is scored separately and far more loosely - most never get mentioned.)
- **CLAUDE.md bloat**: inline entries that are tool/platform/API-specific and belong in `notes/`. These are the highest-value **moves** (relocate every fact, do not trim) - they shrink the every-session prompt without losing anything.
- **Index encoding waste**: the Topical Notes Index in markdown-link form (`- [name](notes/name.md) - hook`) spends ~34 chars per line spelling the name twice. Loss-free to strip, and invisible to any line-length test, so check it before hook length.
- **Bloated index hooks**: Topical Notes Index lines that teach instead of route. In a mature setup the index can be a third of the whole file; capping hooks at ~100 chars is often the second-biggest lever.
- **Orphaned index lines**: a Topical Notes Index entry whose `notes/<topic>.md` file does not exist, or a note file with no index line.
- **Oversized notes**: a single note that has grown large enough to split by sub-topic.
- **Memory without a pointer**: a frontmatter memory file with no matching line in `MEMORY.md` (or a `MEMORY.md` line pointing at a missing file).
- **Cross-tier duplication**: the same fact living in two tiers - keep the more specific copy, drop the redundant one. Find it mechanically (self-citing sections, the `relocated from CLAUDE.md` breadcrumb), never by eyeballing; see `references/audit-checklist.md` check 5.
- **Cross-tier divergence**: two tiers making *incompatible* claims about one subject. More dangerous than duplication - duplication wastes context, contradiction produces wrong actions. The newer dated measurement wins; correct the loser rather than deleting it.
- **Missing recency dates**: new-style notes entries or memory files lacking a date; nudge new additions toward `(YYYY-MM-DD)` / `metadata.updated`.
- **Backup clutter**: stale `~/.claude/CLAUDE.md.bak.*` snapshots the user may want to prune (keep the most recent one or two - they are the preservation safety net).
- **Scope leakage**: a global `notes/` file whose subject is really one repo, or a project memory file holding a fact that is true everywhere. Both directions leak; see `references/audit-checklist.md` check 9.

**Size is the half of the verification that lies.** A relocation is two writes - remove from CLAUDE.md, append to the note - so if the append fails while the removal succeeds, the file gets *smaller* and every size check passes. Shrinking is the failure signature of data loss. Never finish a run on `wc -c` alone: prove each moved block reached its destination (bytes conserved, probe hits, source clean) before reporting any size number, and restore that relocation if it did not. Procedure: `references/verify-after-apply.md`.

Full detail and the routing rubric used to decide where a stray entry should move: `references/audit-checklist.md`, `references/routing-rubric.md`, `references/size-budget.md`, `references/verify-after-apply.md`, and `references/scope-resolution.md`.

## Style
- Use plain hyphens (`-`) only. No em-dashes or en-dashes.
- Never edit `~/.claude/settings.json`.
- Be concise; reference files by absolute path.
