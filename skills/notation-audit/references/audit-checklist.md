# Notation audit checklist

Walk these checks in order. For each finding, record the file path, the problem, and the suggested fix. Group the report by severity: **move** (rebalance a tier), **fix** (broken link / missing pointer), **tidy** (cosmetic / cleanup).

## 1. CLAUDE.md bloat (move - highest value)

Read `~/.claude/CLAUDE.md`. For each inline entry or subsection, ask the routing question (see `routing-rubric.md`): does it apply almost every session across all projects?

- If it is tied to one tool/platform/API/SDK/service -> flag to **move to `~/.claude/notes/<topic>.md`**.
- A whole subsection about a single service is a strong signal: it should usually be a note with a one-line index entry instead.
- Estimate the win: report roughly how many lines would leave the every-session prompt.

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

Spot facts that appear in more than one tier (e.g. a CLI quirk both inline in CLAUDE.md and in a note). Recommend keeping the more specific home and removing the other.

## 6. Backup clutter (tidy)

List `~/.claude/CLAUDE.md.bak.*` snapshots. If there are several, offer to prune the older ones, keeping the most recent one or two.

## Reporting

Render the report with the shared format in `output-format.md`: a scorecard header summarizing the audit scope and the severity tally (`<x> move - <y> fix - <z> tidy`), then one numbered table per severity group (move / fix / tidy) using columns `# - title - severity - problem`. End with the single highest-impact action (usually a CLAUDE.md -> notes move). Offer to apply approved fixes, backing up CLAUDE.md first.
