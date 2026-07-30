# Notation audit checklist

Walk these checks in order. For each finding, record the file path, the problem, and the suggested fix. Group the report by severity: **move** (rebalance a tier), **fix** (broken link / missing pointer), **tidy** (cosmetic / cleanup).

**Preservation first (applies to every fix below).** Notation is additive. Prefer **relocating** content (CLAUDE.md -> notes/, preserving every fact) over trimming it, and **appending** over rewriting. A fix may DELETE an existing line only when that line is factually wrong or directly contradicted by newer notation - and then the finding must name the removal. Never flag a still-true line for deletion just to save space; relocate it instead. See `routing-rubric.md` > "Preservation". Losing a hard-won line is a worse outcome than a slightly long file.

**Net size must not grow (applies to every fix below).** Preservation is not a licence to grow the every-session file. Each finding carries a signed CLAUDE.md character delta, and the run's total must be `<= 0`; when the file is over target the total must be negative enough to land under it. Additive findings (check 2, and any promoted global rule) must be offset by moves in the same run. Full budget and tactics: `size-budget.md`.

## 0. Size budget (sets the goal for the whole run)

Measure before reading anything:

```bash
wc -c ~/.claude/CLAUDE.md
awk '/^## Topical Notes Index/,0' ~/.claude/CLAUDE.md | wc -c   # how much is index
```

Compare against the target in `size-budget.md` (<= 40,000 chars; green band <= 32,000).

- **Over target** -> the run's goal is a projected size under it. Keep working checks 1, 2 and 5 (the reduction levers) until the ledger gets there, or until nothing is left that can move without losing value - then say what is blocking the rest.
- **In the green band** -> no reduction pass needed; just hold the net delta at `<= 0`.
- Report the measured numbers in the scorecard's size ledger either way. Never estimate a size you can `wc -c`.

## 1. CLAUDE.md bloat (move - highest value)

Read `~/.claude/CLAUDE.md`. For each inline entry or subsection, ask the routing question (see `routing-rubric.md`): does it apply almost every session across all projects?

- If it is tied to one tool/platform/API/SDK/service -> flag to **move to `~/.claude/notes/<topic>.md`** (relocate every fact verbatim; this is a move, never a trim).
- A whole subsection about a single service is a strong signal: it should usually be a note with a one-line index entry instead.
- A multi-line inline entry that survives the routing question can still shed its detail: keep the **trigger** inline as one line and move the commands, error strings, and recipe into a note (`size-budget.md` tactic 2).
- Prefer appending to an existing note over creating a new one - a new note also costs a new index line.
- **Report the win in characters, not vibes**: each finding's delta is the byte count of the lines leaving CLAUDE.md, minus any index line it adds.
- The fix is **relocation, not deletion** - the bytes leave CLAUDE.md but land intact in the note. Do not propose dropping detail on the way.

Do NOT flag the genuinely global sections (permissions, gh/git quirks, shell/PATH gotchas, session/harness behavior, workflow preferences, accessibility requirements).

## 2. Topical Notes Index integrity (fix)

Compare the "Topical Notes Index" section in CLAUDE.md against the actual files in `~/.claude/notes/`.

- Index line -> file that does not exist = **orphaned link**, flag to fix (remove the line or restore the file).
- Note file with no index line = **unindexed note**, flag to add a one-line entry. This one **grows** CLAUDE.md - record the positive delta and offset it.
- Index entry whose hook no longer matches the note's content = flag to refresh the description. Refresh it to a router, not a summary.

**Index-line compression (move).** The index routes; it does not teach. Measure the per-line spread (`awk`/`wc` the index section: median length, and how many lines exceed ~100 chars) before quoting a saving - the section total says nothing about how much of it is compressible. Flag lines well over the cap and propose shorter hooks that keep the same routing trigger; any detail worth keeping goes into the note itself, not the index. In a mature setup this is often the second-biggest lever after subsection moves.

**Note consolidation (move).** Several thin sibling notes on one subject can merge into a single topic note, dropping N-1 index lines along with the duplication. Merge content, never discard it.

## 3. Note size and focus (move / tidy)

For each `~/.claude/notes/*.md`:
- If it has grown to cover several unrelated sub-topics, suggest splitting (e.g. `external-apis.md` -> per-service files) and updating the index accordingly.
- If two notes overlap heavily, suggest merging.

## 4. Project memory pointers (fix)

For the current project's memory dir (`~/.claude/projects/<encoded-cwd>/memory/`):
- Each frontmatter memory file should have exactly one pointer line in `MEMORY.md`. Flag files with no pointer (add one) and pointer lines whose target file is missing (remove or restore).
- Flag memory files missing required frontmatter (`name`, `description`, `metadata.type`).
- Flag relative dates ("today", "last month") that should be absolute.

## 5. Cross-tier duplication (move)

Spot facts that appear in more than one tier (e.g. a CLI quirk both inline in CLAUDE.md and in a note). Recommend keeping the more specific home (usually the note) and removing the **redundant copy** - this is the one safe deletion, because the fact survives in the other tier. Before flagging, confirm the two entries are genuinely the same fact and that the surviving copy is at least as complete; if the CLAUDE.md copy has detail the note lacks, merge that detail INTO the note first, then drop the inline copy. Never delete both, and never delete the only copy of a fact.

## 6. Missing recency dates (tidy)

New-style notation carries an absolute date (see `routing-rubric.md` > "Recency timestamps"). Flag, as low-priority tidy:
- `~/.claude/notes/` sections/sub-entries with no `(YYYY-MM-DD)` tag - offer to add today's date to genuinely new additions only (do NOT back-date old content you cannot date accurately; leave undated legacy entries alone).
- Memory files missing `metadata.updated` - offer to add it.
Do not treat undated legacy content as a problem to rewrite; this check only nudges new entries toward dating.

## 7. Backup clutter (tidy)

List `~/.claude/CLAUDE.md.bak.*` snapshots. If there are several, offer to prune the older ones, keeping the most recent one or two. (These `.bak` files are the safety net for the preservation rule above - never prune below the most recent one or two.)

## Reporting

Render the report with the shared format in `output-format.md`: a scorecard header summarizing the audit scope and the severity tally (`<x> move - <y> fix - <z> tidy`), the **size ledger** (measured -> projected -> target), then one numbered table per severity group (move / fix / tidy) using columns `# - title - severity - problem - delta`. End with the single highest-impact action (usually a CLAUDE.md -> notes move). Offer to apply approved fixes, backing up CLAUDE.md first.

**Before offering to apply, check the ledger.** If the approved set nets out `>= 0` chars on `~/.claude/CLAUDE.md`, do not present it as a finished audit - go back and find the offsetting move first. If the file is over target and the best honest projection is still over, say so in one line, give the achievable number, and name what is blocking the rest.

## Verify

After applying, re-measure and report the real before -> after -> target numbers:

```bash
wc -c ~/.claude/CLAUDE.md
```

Never claim a reduction from the projection alone. If the measured result grew, or is still over target, state it plainly and offer the next round.
