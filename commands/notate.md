---
description: Capture this session's learnings and route each one to the right memory tier - global CLAUDE.md, ~/.claude/notes/, per-project MEMORY.md, or project docs. Grounds proposals in the actual project + session, then applies them through an interactive picker. Keeps CLAUDE.md lean.
argument-hint: "[all]"
allowed-tools: ["Read", "Edit", "Write", "Glob", "Bash", "AskUserQuestion"]
disable-model-invocation: true
---

# /notation:notate

Turn what you learned this session into durable, well-placed notation. The job is not "append to CLAUDE.md" - it is to send each learning to the **one tier where it belongs**, defaulting away from CLAUDE.md so it stays small and fast, and to apply only the changes the user actually wants.

**Auto-apply mode.** If `$ARGUMENTS` contains `all`, `--all`, `-y`, or `yes`, run in auto-apply mode: follow Steps 1-5 exactly as written, but in Step 6 skip every `AskUserQuestion` and apply **all** proposals. Still print the proposals/diffs first and still back up `~/.claude/CLAUDE.md` before any inline rule edit. Otherwise run the interactive flow as written.

Read the full decision tree at `${CLAUDE_PLUGIN_ROOT}/skills/notation-audit/references/routing-rubric.md` if a learning is hard to place. The compact version is in Step 3.

## Step 1 - Build the picture (session + project)

Before proposing anything, ground yourself in two sources so proposals are real, deduped, and correctly aimed (global vs *this* project).

**Session (what actually happened):** combine your in-context recall with a light scan of this session's transcript, which catches learnings that scrolled out of context.
```bash
# encoded-cwd = absolute cwd with every "/" replaced by "-" (leading slash included)
enc=$(pwd | sed 's#/#-#g')
tx=$(ls -t ~/.claude/projects/"$enc"/*.jsonl 2>/dev/null | head -1)
echo "transcript: $tx"
```
If `$tx` exists, scan it (do NOT dump the whole file) for the high-signal moments: a command that failed then succeeded, an error string and its resolution, a flag or invocation that got corrected, and any place the user corrected how you worked. `grep -nE '"type":"(user|tool_result)"' "$tx"` and targeted `grep -i` for `error|denied|failed|instead|actually|don.t` are good entry points. Treat recall as primary and the transcript as the safety net.

**Project profile (where things belong + what is already known):**
- `./CLAUDE.md` if the repo tracks one (team conventions already recorded).
- The per-project memory dir's `MEMORY.md` (see Step 5 for how to locate it).
- `git log --oneline -10` and a glance at the project type/structure.

This profile is what makes dedup real instead of guessed, and what lets you tell a global rule apart from a this-project fact.

## Step 2 - Extract candidate learnings as structured proposals

From the picture above, list the candidate learnings. Look for:
- Commands, flags, or invocations that were discovered or corrected
- Gotchas, error messages, and their resolutions
- Config / environment quirks
- Code-style or testing patterns that worked
- Project-specific architecture or decisions not derivable from the code itself
- Corrections the user made to how you worked

Drop anything that is a one-off unlikely to recur, or already present in the project profile, README, or git history. Quality over volume.

Turn each survivor into a **proposal** with these fields - you will reuse them verbatim in Steps 4-6:
- **title** - a short handle (used as the picker option label)
- **tier** - exactly one destination (see Step 3)
- **why** - one line: why this tier and not the next-closest one
- **kind** - `NEW` (add) or `UPDATE` (edit an existing entry in place)
- **confidence** - high / med / low (how sure you are it recurs and is correctly placed)
- **diff** - the concrete text to add or change, and the exact destination path

## Step 3 - Route each learning (do NOT dump)

Assign every proposal's **tier**:

| Signal | Tier | Destination |
| --- | --- | --- |
| High-frequency, cross-project, fires almost every session (permission/CLI/session quirks) | **Global rules** | `~/.claude/CLAUDE.md` (inline) |
| Situational, tied to one tool / platform / API / SDK / service; useful only when that thing comes up | **Topical note** | `~/.claude/notes/<topic>.md` + a line in the Topical Notes Index |
| Specific to THIS project's architecture, decisions, gotchas, or workflow; not in the code | **Project memory** | this project's `MEMORY.md` + a frontmatter memory file |
| A team-shared convention others on the repo need | **Project CLAUDE.md** | `./CLAUDE.md` (only if the repo tracks one) |
| A large guide / spec / phase write-up | **Project docs** | `./.claude/docs/<name>.md` |

**Lean bias (the whole point):** if a learning is tool- or platform-specific, it goes to `notes/`, NOT inline into CLAUDE.md - even if it feels important. Only promote to global CLAUDE.md when it genuinely applies regardless of what you are working on. When in doubt, prefer `notes/` or project memory over CLAUDE.md.

## Step 4 - Dedup against the destination (targeted reads only)

For each proposal, read ONLY the destination file (and the relevant section), not the whole tree. Do not run a repo-wide `find`. Locations are known:
- Global rules + index: `~/.claude/CLAUDE.md`
- Notes: `~/.claude/notes/` (`Glob` it)
- Project memory: the per-project memory dir (see Step 5)
- Project CLAUDE.md / docs: `./CLAUDE.md`, `./.claude/docs/`

If the learning is already covered, mark the proposal `UPDATE` and make the diff an in-place edit rather than a duplicate. If a `notes/` file for the topic already exists, the diff appends to it; only create a new note when no topic file fits. Drop any proposal that turns out to be fully covered already.

## Step 5 - Tier-specific formatting (how each diff should look)

**Topical note (`~/.claude/notes/<topic>.md`):**
- Markdown with `##` section headings and fenced code blocks for commands.
- Pair every note add/create with the **Topical Notes Index** line at the bottom of `~/.claude/CLAUDE.md`: `` - [`notes/<topic>.md`](notes/<topic>.md) - <hook> ``. The index line is the only CLAUDE.md change a note requires, and it does not need the Step 6 backup unless you are also editing rules inline.

**Project memory:**
- Find the per-project memory dir. It is the harness path `~/.claude/projects/<encoded-cwd>/memory/`, where `<encoded-cwd>` is the absolute cwd with every `/` replaced by `-` (leading slash included). Confirm with:
  ```bash
  ls -d ~/.claude/projects/*/memory 2>/dev/null
  ```
  and match the entry whose name encodes the current project path. If none exists for this project, ask the user before creating one.
- One fact per file. Frontmatter:
  ```markdown
  ---
  name: <short-kebab-slug>
  description: <one-line summary for recall relevance>
  metadata:
    type: user | feedback | project | reference
  ---

  <the fact. For feedback/project, add **Why:** and **How to apply:** lines. Link related memories with [[other-slug]].>
  ```
- Convert relative dates ("today", "last week") to absolute (YYYY-MM-DD).
- Pair every memory file with a one-line pointer in that dir's `MEMORY.md`: `- [Title](file.md) - hook`. Never put the fact body in `MEMORY.md`; it is the index only.

**Global CLAUDE.md rule:** one line per concept, in the most relevant existing section. Format `` `<command/pattern>` - <brief note> ``. No verbose prose.

**Project CLAUDE.md / docs:** match the file's existing style.

## Step 6 - Present, then apply through the interactive picker

First **print all proposals as text**, grouped by tier, ordered high-confidence first. For each: `title - kind - confidence`, the one-line **why**, and the short **diff**. (The picker's multi-select has no preview pane, so the diffs must be visible here, above the questions.)

**Auto-apply mode (if `$ARGUMENTS` requested it):** after the printout, skip items 1-2 below entirely - do not call `AskUserQuestion`. Treat every proposal as approved and go straight to item 3 (atomic content+index writes), item 4 (CLAUDE.md backup), and item 5 (summary). The summary should note it auto-applied all N proposals.

Otherwise drive the apply flow with `AskUserQuestion` instead of asking freeform:

1. **Strategy question (single-select).** Ask: "N changes across T tiers - how do you want to apply?" with options:
   - `Apply all` (mark Recommended) - apply every proposal.
   - `Review by tier` - pick individually, tier by tier.
   - `Skip all` - apply nothing.

   If there is only **one** proposal, skip the strategy question and ask a single single-select: `Apply` / `Edit first` / `Skip`.

2. **If `Review by tier`:** for each tier with proposals, ask one **multi-select** question whose options are that tier's proposal titles (with the why as each option's description). If a tier has more than 4 proposals, ask it in successive batches of 4 (the tool caps options at 4). Checked options are applied; unchecked are dropped.

3. **Apply only the approved proposals.** Keep each content change atomic with its index update:
   - a note edit/create together with its Topical Notes Index line,
   - a memory file together with its `MEMORY.md` pointer.

4. **Back up before editing global CLAUDE.md.** If (and only if) an approved change edits `~/.claude/CLAUDE.md` rules inline, snapshot it first:
   ```bash
   cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak.$(date +%Y%m%d-%H%M%S)
   ```
   No backup needed for notes (incl. the index line), memory, or project files.

5. **Summary.** Report what was applied and what was skipped, grouped by tier, referencing files by absolute path.

Never edit `~/.claude/settings.json` (the harness self-grant guard blocks it, and it is not a notation target).

## Output style
- Use plain hyphens (`-`) only. No em-dashes or en-dashes anywhere you write.
- Be concise. Reference files by absolute path.
