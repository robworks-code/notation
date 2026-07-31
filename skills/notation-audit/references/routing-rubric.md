# Notation routing rubric

The full decision tree for placing a learning. Used by `/notation:notate` when capturing and by `notation-audit` when deciding where a misplaced entry should move.

## The core question

> "When will a future session need this, and how often?"

The answer maps to a tier. Frequency and breadth push toward CLAUDE.md; specificity pushes toward notes or memory.

## Step 0 - decide the scope first

Before the tree below, ask:

> Does this stop being true when I switch to another repo?

- **Yes -> project scope.** Skip branches 1 and 2 entirely; choose among branches 3, 4
  and 5 only.
- **No -> global scope.** Branches 1 and 2 apply.

Running the tree first is what produces a scope leak, because a learning can be
tool-shaped **and** repo-bound at once: "our uploads bucket is named lc-prod-uploads and
lives in the us-west Railway project" is repo-specific, so it belongs in project memory,
not the global `notes/railway.md`. But if you ask tier first ("is this tool-shaped?"),
branch 2 files it there, where every other repo's session then loads this repo's
deployment detail. Full rule, the mirror case, and the never-cross list: `scope-resolution.md`.

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
   -> **`./CLAUDE.md`** in the project (only if the repo already has one).

5. **Is it a large, structured write-up** (a spec, a phase summary, an implementation guide)?
   -> **`./.claude/docs/<name>.md`** in the project.

## Tie-breakers

- **Lean bias.** When a learning could plausibly go inline OR into notes, choose notes. CLAUDE.md loads into every prompt; every line there has a recurring cost. Notes load only on demand.
- **Specific beats general.** "Railway buckets need TTL set at create time" is a Railway note, not a global rule, even though it felt important in the moment.
- **One fact, one place.** Do not mirror the same fact across tiers. If it is already in notes, do not also inline it.
- **Project vs global is a scope question, not a tie-break.** It is settled in Step 0
  above, before the tree runs - not as a nudge afterwards. If the fact stops being true
  when you switch repos, it is project-scoped, and a tool-shaped surface does not change
  that. See `scope-resolution.md`.
- **A cheaper home never beats the right home.** `size-budget.md` tactic 3 prefers an
  existing note because a new one costs an index line, and that preference stops at the
  point the existing note is a stretch. The test is this rubric's own purpose: would a
  future session looking for this fact open THAT file? If no, mint the note - the saving
  is about 110 chars and the cost is a fact nobody finds again. Precedence:
  `size-budget.md` > "When two rules conflict".
  <!-- precedence-ref: routing-vs-index-cost -->

## Preservation (never destroy history)

Notation is **additive by default**. Existing lines in `~/.claude/CLAUDE.md` and in project `MEMORY.md` / memory files carry hard-won history; losing them is far more costly than a little duplication or length.

- **An `UPDATE` may DELETE an existing line ONLY when that line is factually wrong, or a newer learning directly contradicts it.** In that case, the removal *is* the point - the stale fact must go. Otherwise, never remove.
- **Superseded-but-still-true content is preserved, not overwritten.** If the new learning extends or refines an existing entry, keep the old line and append the new detail (dated - see below) rather than rewriting the line in place.
- **When an inline CLAUDE.md entry has grown too big, relocate - do not trim.** For `~/.claude/CLAUDE.md`, move the detail into `notes/<topic>.md` (preserving every fact) and leave a one-line index pointer. For a project `./CLAUDE.md`, move it into a project-local home instead (`./.claude/docs/`, the repo's docs, project memory) - never into the global notes. Relocation keeps the information; trimming loses it.
- **Prefer `NEW`-append or move-to-notes over `UPDATE`-rewrite.** Reach for an in-place rewrite only for the narrow wrong/contradicted case above. A bias toward `UPDATE` is what silently erases history - default away from it.
- **Never condense two true facts into one lossy summary.** If both still hold, both stay.

When a removal genuinely is warranted (wrong/contradicted), say so explicitly in the proposal's `why` ("removes X - contradicted by Y") so the deletion is visible and justified, never incidental.

**Preservation is not a licence to grow `~/.claude/CLAUDE.md`.** Additive means facts are never
lost, not that the every-session file only ever gets bigger - relocation to `notes/` is how both
hold at once. The `notation-audit` skill enforces a hard size budget on that file (net delta `<= 0`
on every run, target <= 40,000 chars): see `size-budget.md`.

That budget is the **global** file's alone. A project `./CLAUDE.md` loads only in its own repo, so
it has room to grow - silent under 20,000 chars, advisory to 40,000, and strict only when the user
asks or a project memory records that preference. When a project file does need to shed weight, its
detail goes to `./.claude/docs/`, the repo's
own docs, or project memory - **never to `~/.claude/notes/`**, which would leak one repo's specifics
into every other session.

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
