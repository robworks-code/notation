# notation

A Claude Code plugin for keeping your AI memory tidy and well-placed.

Most "update CLAUDE.md" commands dump everything into one file. `notation` does the opposite: it **routes each learning to the tier where it belongs**, with a deliberate bias toward keeping `CLAUDE.md` lean so it does not bloat the every-session prompt.

## Tiers it manages

| Tier | Location | For |
| --- | --- | --- |
| Global rules | `~/.claude/CLAUDE.md` | High-frequency, cross-project rules that fire almost every session |
| Topical notes | `~/.claude/notes/*.md` | Tool / platform / API-specific gotchas, loaded on demand, indexed in CLAUDE.md |
| Project memory | `~/.claude/projects/<project>/memory/` | Per-project facts, one per frontmatter file, indexed by `MEMORY.md` |
| Project docs | `./.claude/docs/`, `./CLAUDE.md` | Team-shared guides and conventions tracked in the repo |

## What you get

### `/notation:notate`
Capture this session's learnings and route each one to the correct tier. It first **reads the session** - classifying its type, gauging how many learnings there are, and noticing which tiers were actually exercised - then right-sizes the flow: a thin session early-exits, a single clear learning skips straight to one confirm, and a rich session runs the full process. It announces the flow it chose in one line; pass `full` to force the complete flow. It grounds itself in the real context - scanning the session transcript for learnings that scrolled out of view and reading the project's own `CLAUDE.md`, `MEMORY.md`, and recent git history - so each proposal is deduped and correctly aimed at global vs *this* project. Every learning becomes a structured proposal (tier, rationale, new-or-update, confidence, concrete diff), presented as a scorecard header plus per-tier tables with the diffs below. It then applies them through a plan-mode-style interactive picker: `Apply all`, `Review by tier` (multi-select per tier), or `Skip all`. It backs up `CLAUDE.md` before editing it and keeps indexes in sync (Topical Notes Index, `MEMORY.md` pointers).

### `/notation:notate-all` (or `/notation:notate all`)
Same session read, routing, and presentation as `/notation:notate`, but it skips the strategy picker and applies **every** proposal automatically. It still does the adaptive read (session type, tier focus, and early-exit on a thin session) and still prints the full proposal list with diffs first and backs up `CLAUDE.md` before any inline edit - you just are not asked which to apply. Use it when you trust the routing and want a one-shot save at the end of a session.

### `notation-audit` skill
Auto-invocable health check. Ask it to "audit my notes" or "check CLAUDE.md for bloat" and it reports inline entries that should move to notes, orphaned index links, oversized notes, memory files missing pointers, cross-tier duplication, and stale backups - then offers targeted fixes.

### `/notation:feedback`
Send feedback about the plugin - a bug, an idea, or a routing correction that went wrong - straight to the maintainer as a support ticket. It attaches lightweight context (plugin version, OS, and a short note on what notation did this session), shows you the exact payload, and **always confirms before sending**. Anonymous by default; add your email only if you want a reply.

## How it preserves your notes

`notation` is **additive by default**. It never rewrites or drops a still-true line in `CLAUDE.md` or your memory files to save space - an in-place removal happens only when a line is factually wrong or directly contradicted by a newer learning. When an inline entry has just grown too big, it **relocates** the detail into a topical note (every fact intact) rather than trimming it. New notes and memory entries are stamped with the date they were added (`(YYYY-MM-DD)` in notes, `updated:` in memory frontmatter) so recency is always visible.

## Install

```
claude plugin marketplace add ringo380/robworks-claude-code-plugins
claude plugin install notation@robworks-claude-code-plugins
```

Then run `/notation:notate` at the end of a work session.

## License

MIT - see [LICENSE](LICENSE).
