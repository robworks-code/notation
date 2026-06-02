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
Capture this session's learnings and route each one to the correct tier. It dedups against the destination, backs up `CLAUDE.md` before editing it, keeps indexes in sync (Topical Notes Index, `MEMORY.md` pointers), shows grouped proposals, and applies only what you approve.

### `notation-audit` skill
Auto-invocable health check. Ask it to "audit my notes" or "check CLAUDE.md for bloat" and it reports inline entries that should move to notes, orphaned index links, oversized notes, memory files missing pointers, cross-tier duplication, and stale backups - then offers targeted fixes.

## Install

```
claude plugin marketplace add ringo380/robworks-claude-code-plugins
claude plugin install notation@robworks-claude-code-plugins
```

Then run `/notation:notate` at the end of a work session.

## License

MIT - see [LICENSE](LICENSE).
