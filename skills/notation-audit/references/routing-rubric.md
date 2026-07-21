# Notation routing rubric

The full decision tree for placing a learning. Used by `/notation:notate` when capturing and by `notation-audit` when deciding where a misplaced entry should move.

## The core question

> "When will a future session need this, and how often?"

The answer maps to a tier. Frequency and breadth push toward CLAUDE.md; specificity pushes toward notes or memory.

## Decision tree

1. **Does it apply almost every session, regardless of what I am working on?**
   (permission-hook behavior, gh/git CLI quirks, shell/PATH gotchas, session-harness bugs, global workflow rules)
   -> **Global `~/.claude/CLAUDE.md`**, inline, one line per concept.

2. **Is it tied to a specific tool, platform, API, SDK, service, or registrar** - useful only when that thing is in play?
   (a cloud provider's quirk, one CLI's auth flow, one library's gotcha, one MCP server's behavior)
   -> **`~/.claude/notes/<topic>.md`** + a line in the Topical Notes Index. This is the default home for most discoveries.

3. **Is it specific to the current project** - its architecture, a decision, a non-obvious gotcha, a workflow - and NOT derivable from the code, README, or git history?
   -> **Project memory**: a frontmatter file in `~/.claude/projects/<encoded-cwd>/memory/` + a pointer line in `MEMORY.md`.

4. **Is it a convention the rest of the team/repo needs** (build/test/deploy steps, architecture orientation)?
   -> **`./CLAUDE.md`** in the project (only if the repo tracks one).

5. **Is it a large, structured write-up** (a spec, a phase summary, an implementation guide)?
   -> **`./.claude/docs/<name>.md`** in the project.

## Tie-breakers

- **Lean bias.** When a learning could plausibly go inline OR into notes, choose notes. CLAUDE.md loads into every prompt; every line there has a recurring cost. Notes load only on demand.
- **Specific beats general.** "Railway buckets need TTL set at create time" is a Railway note, not a global rule, even though it felt important in the moment.
- **One fact, one place.** Do not mirror the same fact across tiers. If it is already in notes, do not also inline it.
- **Project vs global.** If the fact stops being true when you switch repos, it is project memory, not global.

## Preservation (never destroy history)

Notation is **additive by default**. Existing lines in `~/.claude/CLAUDE.md` and in project `MEMORY.md` / memory files carry hard-won history; losing them is far more costly than a little duplication or length.

- **An `UPDATE` may DELETE an existing line ONLY when that line is factually wrong, or a newer learning directly contradicts it.** In that case, the removal *is* the point - the stale fact must go. Otherwise, never remove.
- **Superseded-but-still-true content is preserved, not overwritten.** If the new learning extends or refines an existing entry, keep the old line and append the new detail (dated - see below) rather than rewriting the line in place.
- **When an inline CLAUDE.md entry has grown too big, relocate - do not trim.** Move the detail into `notes/<topic>.md` (preserving every fact) and leave a one-line index pointer. Relocation keeps the information; trimming loses it.
- **Prefer `NEW`-append or move-to-notes over `UPDATE`-rewrite.** Reach for an in-place rewrite only for the narrow wrong/contradicted case above. A bias toward `UPDATE` is what silently erases history - default away from it.
- **Never condense two true facts into one lossy summary.** If both still hold, both stay.

When a removal genuinely is warranted (wrong/contradicted), say so explicitly in the proposal's `why` ("removes X - contradicted by Y") so the deletion is visible and justified, never incidental.

## Recency timestamps

New entries carry an absolute date so a future session can tell recent notation from old. Use the machine date, not a guess: `date +%Y-%m-%d`.

- **Topical notes.** Tag each new sub-entry or `##` section with an inline `(YYYY-MM-DD)`, e.g. a heading `## Bucket TTL (2026-07-21)` or a bullet ending ` (2026-07-21)`. When appending to an existing note, date only the appended lines - do not restamp the whole file.
- **Project memory.** Add an `updated: YYYY-MM-DD` line under `metadata:` in the frontmatter (and set it again whenever the file is edited). This is the recency signal for the memory tier.
- **Global CLAUDE.md.** Do NOT date inline rules - the every-session file stays clean and dateless. Recency for global rules is not worth the visual noise.
- Dates are ASCII digits and hyphens only; never introduce Unicode or en/em dashes into a date.

## Memory type field

When writing a project memory file, set `metadata.type`:
- `user` - who the user is (role, expertise, durable preferences).
- `feedback` - guidance on how to work (corrections, confirmed approaches). Include **Why:** and **How to apply:**.
- `project` - ongoing work, goals, constraints not in the code. Convert relative dates to absolute.
- `reference` - pointers to external resources (URLs, dashboards, tickets).

## What never gets saved

- Anything the code, README, or git history already records.
- One-off fixes unlikely to recur.
- Secrets or credentials (store those in the user's secret manager, not notation).
