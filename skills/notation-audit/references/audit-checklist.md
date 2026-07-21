# Notation audit checklist

Walk these checks in order. For each finding, record the file path, the problem, and the suggested fix. Group the report by severity: **move** (rebalance a tier), **fix** (broken link / missing pointer), **tidy** (cosmetic / cleanup).

**Preservation first (applies to every fix below).** Notation is additive. Prefer **relocating** content (CLAUDE.md -> notes/, preserving every fact) over trimming it, and **appending** over rewriting. A fix may DELETE an existing line only when that line is factually wrong or directly contradicted by newer notation - and then the finding must name the removal. Never flag a still-true line for deletion just to save space; relocate it instead. See `routing-rubric.md` > "Preservation". Losing a hard-won line is a worse outcome than a slightly long file.

## 1. CLAUDE.md bloat (move - highest value)

Read `~/.claude/CLAUDE.md`. For each inline entry or subsection, ask the routing question (see `routing-rubric.md`): does it apply almost every session across all projects?

- If it is tied to one tool/platform/API/SDK/service -> flag to **move to `~/.claude/notes/<topic>.md`** (relocate every fact verbatim; this is a move, never a trim).
- A whole subsection about a single service is a strong signal: it should usually be a note with a one-line index entry instead.
- Estimate the win: report roughly how many lines would leave the every-session prompt.
- The fix is **relocation, not deletion** - the bytes leave CLAUDE.md but land intact in the note. Do not propose dropping detail on the way.

Do NOT flag the genuinely global sections (permissions, gh/git quirks, shell/PATH gotchas, session/harness behavior, workflow preferences).

## 2. Topical Notes Index integrity (fix)

Compare the "Topical Notes Index" section in CLAUDE.md against the actual files in `~/.claude/notes/`.

- Index line -> file that does not exist = **orphaned link**, flag to fix (remove the line or restore the file).
- Note file with no index line = **unindexed note**, flag to add a one-line entry.
- Index entry whose hook no longer matches the note's content = flag to refresh the description.

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

Render the report with the shared format in `output-format.md`: a scorecard header summarizing the audit scope and the severity tally (`<x> move - <y> fix - <z> tidy`), then one numbered table per severity group (move / fix / tidy) using columns `# - title - severity - problem`. End with the single highest-impact action (usually a CLAUDE.md -> notes move). Offer to apply approved fixes, backing up CLAUDE.md first.
