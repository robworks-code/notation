# notation

A Claude Code plugin for keeping your AI memory tidy and well-placed.

Most "update CLAUDE.md" commands dump everything into one file. `notation` does the opposite: it **routes each learning to the tier where it belongs**, with a deliberate bias toward keeping `CLAUDE.md` lean so it does not bloat the every-session prompt.

## Tiers it manages

| Tier | Location | For |
| --- | --- | --- |
| Global rules | `~/.claude/CLAUDE.md` | High-frequency, cross-project rules that fire almost every session |
| Topical notes | `~/.claude/notes/*.md` | Tool / platform / API-specific gotchas, loaded on demand, indexed in CLAUDE.md |
| Project memory | `~/.claude/projects/<encoded-cwd>/memory/` | Per-project facts, one per frontmatter file, indexed by `MEMORY.md` |
| Project docs | `./.claude/docs/`, `./CLAUDE.md` | Team-shared guides and conventions tracked in the repo |

## What you get

### `/notation:notate`
Capture this session's learnings and route each one to the correct tier. It first **reads the session** - classifying its type, gauging how many learnings there are, and noticing which tiers were actually exercised - then right-sizes the flow: a thin session early-exits, a single clear learning skips straight to one confirm, and a rich session runs the full process. It announces the flow it chose in one line; pass `full` to force the complete flow. It grounds itself in the real context - scanning the session transcript for learnings that scrolled out of view and reading the project's own `CLAUDE.md`, `MEMORY.md`, and recent git history - so each proposal is deduped and correctly aimed at global vs *this* project. Every learning becomes a structured proposal (tier, rationale, new-or-update, confidence, concrete diff), presented as a scorecard header plus per-tier tables with the diffs below. It then applies them through a plan-mode-style interactive picker: `Apply all`, `Review by tier` (multi-select per tier), or `Skip all`. It backs up `CLAUDE.md` before editing it and keeps indexes in sync (Topical Notes Index, `MEMORY.md` pointers). Capture is budgeted too: it measures `~/.claude/CLAUDE.md` up front, prices every global-tier proposal in characters, and **closes the global tier by default once the file is at or over ~40,000 chars** - borderline learnings route to `notes/` instead. When something does land inline, it re-measures and reports the real before -> after size rather than trusting the estimate.

### `/notation:notate-all` (or `/notation:notate all`)
Same session read, routing, and presentation as `/notation:notate`, but it skips the strategy picker and applies **every** proposal automatically. It still does the adaptive read (session type, tier focus, and early-exit on a thin session), still prints the full proposal list with diffs first, still enforces the CLAUDE.md budget gate, and still backs up `CLAUDE.md` before any inline edit - you just are not asked which to apply. Because no picker stands between a proposal and the file here, it re-measures `CLAUDE.md` afterward and reports the size in the summary. Use it when you trust the routing and want a one-shot save at the end of a session.

### `notation-audit` skill
Auto-invocable health check. Ask it to "audit my notes" or "check CLAUDE.md for bloat" and it reports inline entries that should move to notes, bloated index hooks, orphaned index links, oversized notes, memory files missing pointers, cross-tier duplication, and stale backups - then offers targeted fixes.

The audit is **budgeted**: it measures `~/.claude/CLAUDE.md` with `wc -c` up front, scores every finding with its signed character delta, and holds the run's net delta at `<= 0` - an audit can never leave the every-session file bigger than it found it. If the file is over the ~40,000-char warning threshold, the audit keeps proposing relocations until the projection lands under it, and re-measures afterward instead of trusting the projection. Additive fixes (a missing index line) are counted and offset by moves in the same run. It hits the budget by **branching detail out into linked note files**, never by deleting a still-true line - if the target can only be met by losing a fact, it misses the target and says why.

**A project's own `./CLAUDE.md` is treated the opposite way.** It loads only inside its own repo, so it gets headroom rather than a leash: silent under 20,000 chars, a single advisory line up to 40,000, and only past that a real finding - which is still advisory, and which relocates detail to project-local homes (`./.claude/docs/`, the repo's docs, project memory) rather than into your global notes. There is no no-growth rule for a project file. If you do want it held to the same strict standard, ask for it ("audit this repo strictly") or record the preference in that project's memory and it sticks for future sessions.

**Every relocation is proved, not assumed.** A move is two writes - remove from `CLAUDE.md`, append to the note - so if the append fails while the removal succeeds, the file gets *smaller* and a size check passes. Shrinking is the failure signature of data loss. So before applying, the audit backs up every file that will lose content and picks one or two distinctive strings from each block being moved (an error message, a sha, a flag - never a common word). Afterward it checks that the destination **grew by at least the bytes that left** (a point probe cannot catch a truncated tail), that each string now hits its destination, and that it is **gone from the source** - the inverse failure, where the append lands but the removal does not, otherwise looks just like an under-delivering estimate. If a check misses, it restores that one relocation and reports the loss rather than the size win. Rewrites that legitimately shorten text in place are classified as compressions and not probed, so a correct edit is never destroyed by a false failure.

Character deltas are **measured, not felt**: each row's number is a real byte count of the content being removed, minus a replacement line that is actually drafted at report time rather than imagined. Rows whose replacement length was assumed instead are marked with a `~`, and the projected total is labelled an estimate - the audit expects to converge over two or three passes and says so, instead of promising a landing it cannot make in one.

### `/notation:feedback`
Send feedback about the plugin - a bug, an idea, or a routing correction that went wrong - straight to the maintainer as a support ticket. It attaches lightweight context (plugin version, OS, and a short note on what notation did this session), shows you the exact payload, and **always confirms before sending**. Anonymous by default; add your email only if you want a reply.

## How it preserves your notes

`notation` is **additive by default**. It never rewrites or drops a still-true line in `CLAUDE.md` or your memory files to save space - an in-place removal happens only when a line is factually wrong or directly contradicted by a newer learning. When an inline entry has just grown too big, it **relocates** the detail into a topical note (every fact intact) rather than trimming it. New notes and memory entries are stamped with the date they were added (`(YYYY-MM-DD)` in notes, `updated:` in memory frontmatter) so recency is always visible.

## Install

```
claude plugin marketplace add robworks-code/robworks-claude-code-plugins
claude plugin install notation@robworks-claude-code-plugins
```

Then run `/notation:notate` at the end of a work session.

## License

MIT - see [LICENSE](LICENSE).
