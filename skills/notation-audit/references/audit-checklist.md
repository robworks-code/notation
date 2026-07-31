# Notation audit checklist

Walk these checks in order. For each finding, record the file path, the problem, and the suggested fix. Group the report by severity: **move** (rebalance a tier), **fix** (broken link / missing pointer), **tidy** (cosmetic / cleanup).

**Preservation first (applies to every fix below).** Notation is additive. Prefer **relocating** content (preserving every fact) over trimming it - global-file content goes to `~/.claude/notes/`, project-file content to project-local homes (check 8) - and **appending** over rewriting. A fix may DELETE an existing line only when that line is factually wrong or directly contradicted by newer notation - and then the finding must name the removal. Never flag a still-true line for deletion just to save space; relocate it instead. See `routing-rubric.md` > "Preservation". Losing a hard-won line is a worse outcome than a slightly long file.

**Net size of the GLOBAL file must not grow (applies to every fix below).** Preservation is not a licence to grow the every-session file. Each finding carries a signed character delta against `~/.claude/CLAUDE.md`, and the run's total must be `<= 0`; when the file is over target the total must be negative enough to land under it. Additive findings (check 2, and any promoted global rule) must be offset by moves in the same run. Full budget and tactics: `size-budget.md`.

**This rule is about `~/.claude/CLAUDE.md` only.** A project's own `./CLAUDE.md` has a soft, advisory budget with real headroom - see check 8. Checks 1, 2 and 5 below all operate on the global file; do not run them against a project file - **except check 5's cross-scope half** ("Compare across scopes too"), which deliberately compares project memory against the global notes to find the same fact filed in both scopes. That half reads project files by design; it is exempt because it **relocates nothing into the global tier** - both copies already exist, and it only deletes the redundant one. Which copy that is depends on the fact's own scope, not on a fixed direction: a repo-bound fact loses its *global* copy, a globally-true fact loses its *project* copy (check 5, "Keep the copy whose scope matches the fact"). Deleting the global copy of an everywhere-true fact would strand it in one repo - the leak check 9's second bullet exists to fix. (Under strict mode, check 8 scores the project file against the global file's *rules* - it still never runs checks 1, 2 or the global-tier half of 5, because those relocate into the global `~/.claude/notes/`.)

## 0. Size budget (sets the goal for the whole run)

Measure before reading anything:

```bash
wc -c ~/.claude/CLAUDE.md
awk '/^## Topical Notes Index/,0' ~/.claude/CLAUDE.md | wc -c   # how much is index
wc -c ./CLAUDE.md 2>/dev/null                                   # project file, if the repo has one
```

Compare the global file against the target in `size-budget.md` (<= 40,000 chars; green band <= 32,000).

- **Over target** -> the run's goal is a projected size under it. Keep working checks 1, 2 and 5 (the reduction levers) until the ledger gets there, or until nothing is left that can move without losing value - then say what is blocking the rest.
- **In the green band** -> no reduction pass needed; just hold the net delta at `<= 0`.
- Report the measured numbers in the scorecard's size ledger either way. Never estimate a size you can `wc -c`.
- The project file is scored separately by check 8, under its own much looser rules.

## 1. Global CLAUDE.md bloat (move - highest value)

Read `~/.claude/CLAUDE.md`. For each inline entry or subsection, ask the routing question (see `routing-rubric.md`): does it apply almost every session across all projects?

- If it is tied to one tool/platform/API/SDK/service -> flag to **move to `~/.claude/notes/<topic>.md`** (relocate every fact verbatim; this is a move, never a trim).
- A whole subsection about a single service is a strong signal: it should usually be a note with a one-line index entry instead.
- A multi-line inline entry that survives the routing question can still shed its detail: keep the **trigger** inline as one line and move the commands, error strings, and recipe into a note (`size-budget.md` tactic 2).
- Prefer appending to an existing note over creating a new one - a new note also costs a new index line.
- **Report the win in characters, not vibes**: each finding's delta is the measured byte count of the lines leaving CLAUDE.md, minus the **drafted** replacement (the pointer line, the index line). Draft the replacement at report time - it is one line, and it is the substance of the proposal anyway - so both halves of the number are real. Per-tactic methods: `size-budget.md` > "Every row's delta needs a method".
- The fix is **relocation, not deletion** - the bytes leave CLAUDE.md but land intact in the note. Do not propose dropping detail on the way.

Do NOT flag the genuinely global sections (permissions, gh/git quirks, shell/PATH gotchas, session/harness behavior, workflow preferences, accessibility requirements).

## 2. Topical Notes Index integrity and weight (fix / move)

Compare the "Topical Notes Index" section in CLAUDE.md against the actual files in `~/.claude/notes/`. The first three checks below are **fix** findings; the last two are **move** findings - group each row under the severity it carries, not under this heading's, so the scorecard tally stays honest.

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

**Compare across scopes too, not just across global tiers.** A fact can sit in project memory *and* in a global note. Keep the copy whose scope matches the fact - if it stops being true in another repo, project memory is the survivor and the global note's copy is the redundant one, not the reverse. Removing the global copy is the safe deletion here because the fact survives in project memory; removing the project copy would leave a repo-bound fact loaded in every session.

## 6. Missing recency dates (tidy)

New-style notation carries an absolute date (see `routing-rubric.md` > "Recency timestamps"). Flag, as low-priority tidy:
- `~/.claude/notes/` sections/sub-entries with no `(YYYY-MM-DD)` tag - offer to add today's date to genuinely new additions only (do NOT back-date old content you cannot date accurately; leave undated legacy entries alone).
- Memory files missing `metadata.updated` - offer to add it.
Do not treat undated legacy content as a problem to rewrite; this check only nudges new entries toward dating.

## 7. Backup clutter (tidy)

Backups fall into **two classes with opposite treatment**, and the whole check is sorting
them correctly. Get it wrong and the audit proposes destroying history.

**Ownership is what separates them, and path is a reliable proxy for ownership only
because notation writes nowhere else.** Everything under `~/.claude/notation-backups/` is
written by this tool (`verify-after-apply.md` check 0); everything outside it belongs to
the user. Do not weaken that rule by writing a backup beside an original - the moment the
two share a filename pattern, no check can tell them apart.

- **The user's own backups** - anything matching `*.bak.*` outside `notation-backups/`,
  whether a hand-made `~/.claude/CLAUDE.md.bak.<stamp>` before a large edit or a
  `~/.claude/notes/<topic>.md.bak.<stamp>`. Frequently the only record of what a file
  said before an edit. **Never propose deleting one**, and never assume one is
  notation's just because the filename looks familiar.
- **Notation run backups** - one directory per run under `notation-backups/`, holding the
  sources that run copied before writing. Spent once that run's checks passed. These are
  the only backups this check may offer to remove.

### List every family

```bash
find ~/.claude -maxdepth 1 -name 'CLAUDE.md.bak.*' 2>/dev/null          # 1 user snapshots
find ~/.claude/notes -maxdepth 1 -name '*.md.bak.*' 2>/dev/null         # 2 user note backups
enc=$(printf '%s' "$PWD" | sed 's#[/.]#-#g')
find ~/.claude/notation-backups/global ~/.claude/notation-backups/"$enc" \
     -mindepth 1 -maxdepth 1 -type d 2>/dev/null                        # 3 run dirs, this run's scopes
printf 'other projects with backups: %s\n' \
  "$(find ~/.claude/notation-backups -mindepth 1 -maxdepth 1 -type d \
     -not -name "$enc" -not -name global 2>/dev/null | wc -l | tr -d ' ')"   # 4 count only
du -sh ~/.claude/notation-backups 2>/dev/null
find . -maxdepth 1 -name 'CLAUDE.md.bak.*' 2>/dev/null                  # 5 in-repo, always a defect
```

Use `find`, not a bare `ls` glob. The Bash tool runs zsh, where a glob matching nothing
aborts with `no matches found` **before the command runs** - and `2>/dev/null` does not
suppress it, because the error is the shell's, not `ls`'s. The normal state here is "no
backups", so a glob recipe prints an error on the healthy path. For the same reason every
command in this check ends `2>/dev/null` and, where it can exit non-zero on the healthy
path, `|| true` - a check that reports an error when nothing is wrong teaches the reader
to ignore its own output.

### Which run backups are safe to remove

Only a run directory containing a `.verified` marker. Check 0 writes that marker after,
and only after, the run's preservation checks passed:

```bash
find ~/.claude/notation-backups -mindepth 2 -maxdepth 2 -type d 2>/dev/null | while read -r d; do
  [ -f "$d/.verified" ] && printf 'spent    %s\n' "$d" || printf 'KEEP     %s\n' "$d"
done
```

A directory with no marker is a run that failed, was interrupted, or was restored - its
contents are the only remaining copy of whatever that run moved. **Never offer to delete
one, and never fall back to age as a proxy**: the oldest directory is exactly as likely
to be the failed run whose backup is load-bearing. If unmarked directories are piling up,
that is a finding about failed runs, not about clutter.

### Defer to an existing rotation policy - for the user's own backups

```bash
ls ~/.claude/bin/rotate-backups.sh 2>/dev/null || true
/usr/bin/grep -n -i 'rotate-backups\|prune-days' ~/.claude/CLAUDE.md 2>/dev/null || true
```

If either turns up a policy, **the user has already reasoned about this and their policy
wins.** Report families 1 and 2 as one informational ledger line - count, total size, how
many are already compressed - and raise no finding *for those families*. Do not restate
their policy back to them as a proposal, and never contradict it: a real setup found this
way keeps the 10 newest uncompressed for diffing, gzips the rest, and deletes nothing
without an explicit age threshold. An audit that read its own advice literally against
that setup would have proposed deleting 103 of 105 files.

**The deference stops there.** It covers the families the policy is about and nothing
else. A rotation script for `~/.claude/CLAUDE.md.bak.*` says nothing about a stray backup
sitting in a repo working tree, and suppressing family 5 because family 1 is managed
would silence the one finding here that is about to be committed to someone's repo.

### What may be proposed, per family

1. **User snapshots** (`~/.claude/CLAUDE.md.bak.*`) - informational only, always. Absent a
   rotation policy and with a large count, the safe offer is **compression** (`gzip -9`
   all but the newest few), which is lossless and reversible. Deletion only if the user
   asks and only with an age threshold they name - never a count this skill invented.
   `keep the most recent one or two` was that invented number; it is gone.
2. **User note backups** (`~/.claude/notes/*.md.bak.*`) - same treatment as family 1.
   Notation no longer writes here, so any file matching this pattern is the user's. They
   do not match `*.md` and are never misread as notes.
3. **Notation run directories** - offer to delete only those carrying `.verified`, and
   name each one individually. Never prune the current run's directory before its own
   verification has passed: that is the safety net the run in progress depends on.
4. **Other projects' run directories** - report the count and the tree's total size, then
   stop. **Never delete another project's backups**: you cannot verify from here that its
   runs passed, and by design an audit resolves only the current project
   (`scope-resolution.md`). The count above excludes this project and `global/`, so it is
   not double-counting family 3.
5. **A backup inside the repo working tree** (`./CLAUDE.md.bak.*`) is a defect, not
   clutter: report it, offer to **move** it under
   `~/.claude/notation-backups/<enc>/recovered/`, and note that plugin versions before
   0.11.0 wrote backups beside their originals. Move it - do not delete it - and never
   delete a stray one you did not create. This family is reported even when a rotation
   policy exists.

**A `.bak` deletion is a real deletion.** It gets everything check 5's deletions get:
named individually in the report, justified by a `.verified` marker rather than by age,
applied only on explicit approval, and never bundled incidentally into another finding.

## 8. Project CLAUDE.md weight (advisory)

Only if `./CLAUDE.md` **exists** in the current repo. Test for the file, not for git: `wc -c ./CLAUDE.md 2>/dev/null`. The harness loads it whether or not it is committed, and many users gitignore it - so `git ls-files` is the wrong predicate and would skip a present, loaded, oversized file. This file loads only inside its own repo, so it gets headroom, not a leash - see `size-budget.md` > "Project CLAUDE.md" for the full rule.

The three bands below are the **advisory** (default) procedure. Strict mode replaces them - see the end of this check.

- **Under 20,000 chars** -> **silent**. Do not report a size, do not propose a trim, do not mention it at all. This is the normal state and is not a finding.
- **20,000 to 40,000** -> **one advisory ledger line, zero findings**: `./CLAUDE.md: 24,180 chars (soft cap 40,000) - fine, no action`. Do not manufacture moves. A large or long-lived codebase legitimately lives here.
- **Over 40,000** -> a real **move** finding. Propose relocation into project-local homes (`./.claude/docs/<name>.md` first, then the repo's real docs, then project memory) - **never into `~/.claude/notes/`**, which is global and would leak this repo's specifics into every other one. Leave a one-line pointer behind. Report a projected size.

Even over 40,000 this stays **advisory**: the user may decline, and the audit accepts that without re-raising it in the same run. There is no no-growth rule for a project file - a run that grows `./CLAUDE.md` is not a failed run.

**Strict mode** applies the global file's rules (net delta `<= 0`, reduce until under target) to `./CLAUDE.md`, but only when the user asks in this run, or a `project`-type memory file for this repo records that preference. Precedence and how to record it: `size-budget.md` > "Strict mode for a project file".

When strict is on it **replaces all three bands**, including the silent one: always print the project ledger line and always score the file, even under 20,000 chars. Say in the scorecard which trigger fired - `strict (requested)` or `strict (project memory)` - so it is obvious which rules produced the findings. Relocation destinations do not change: still project-local, never `~/.claude/notes/`.

## 9. Scope leakage (move)

Content in the scope that does not match the fact. Both directions are real, and neither is caught by any check above. Full definitions and the never-cross list: `scope-resolution.md`.

When the fact appears in only one location (the wrong scope) - if it already exists in both scopes, check 5 handles the mismatch instead:

- **A global note whose subject is one repo.** `~/.claude/notes/<topic>.md` is about a tool, platform, API, SDK, or service. Signals: the note names a repo, a repo-local path, a service name that exists only in one project, or a deployment detail true of exactly one deploy. Flag to **move** into that project's memory (or `./.claude/docs/` if it is long-form), leaving the genuinely tool-general parts behind. Only propose this when the project is identifiable - if the note does not say which repo it belongs to, flag it `tidy` and ask, rather than guessing a destination.
- **Project memory holding a global fact.** A memory file that would stay true in any repo belongs in `~/.claude/notes/` or, if it fires every session, inline. Flag to move and drop the `MEMORY.md` pointer with it. This is the named exception to never-cross rule 2 (`scope-resolution.md`): the rule forbids relocating project-**scoped** content globally, and this fact was never project-scoped - it was only filed that way. The memory file is a **project-scope source** and must be backed up to `~/.claude/notation-backups/<encoded-cwd>/` before the removal, like any other source (`verify-after-apply.md` check 0).
- **A project fact duplicated into a global note.** Handled as check 5's cross-scope case; count it there, not twice.

**A whole note is rarely uniformly misfiled.** The usual shape is a tool note with two or three repo-bound entries in it. Propose moving those entries, not the file - and relocate them verbatim, under the same preservation rule as every other move.

Deltas from this check are per-file and never pooled with the other scope's - a global note shrinking does not pay for project memory growing, and neither feeds the global CLAUDE.md no-growth gate unless the row actually touches `~/.claude/CLAUDE.md` (it does when a note is emptied entirely and its index line goes with it). Carry a note-file row in the report's `file` column as `notes`, never `global` - `global` is reserved for rows against `~/.claude/CLAUDE.md` and is what the gate sums (`output-format.md` > Zone 2).

## Reporting

Render the report with the shared format in `output-format.md`: a scorecard header summarizing the audit scope and the severity tally (`<x> move - <y> fix - <z> tidy`), the **size ledger** (measured -> projected -> target), then one numbered table per severity group (move / fix / tidy) using columns `# - title - severity - problem - delta`. End with the single highest-impact action (usually a CLAUDE.md -> notes move). Offer to apply approved fixes, backing up CLAUDE.md first.

**Before offering to apply, check the ledger.** Count only the rows whose delta is against `~/.claude/CLAUDE.md`; project-file rows are excluded from this gate entirely (they have no no-growth rule unless strict is on, in which case they get their own separate `<= 0` check). If the approved global set nets out `>= 0` chars, do not present it as a finished audit - go back and find the offsetting move first. If the file is over target and the best honest projection is still over, say so in one line, give the achievable number, and name what is blocking the rest.

## Verify

Two checks after applying, in this order. Full procedure: `verify-after-apply.md`.

**1. Preservation checks (can fail the run).** For every applied **relocation** - not a compression; tactics 5 and 7 rewrite in place and must not be probed - confirm two things. First, the destination file **grew by at least the byte count that left the source**; a shortfall is a partial write that no point probe can catch. Second, 1-2 distinctive strings picked *before* applying (an error string, a sha, a flag, a number - never a common word, and never one spanning a line break) now hit their own destination file with `/usr/bin/grep -c -F`, and are **gone from the source** - the inverse failure, where the append lands but the removal does not, otherwise passes silently as an under-delivering estimate. Assert the preconditions beforehand: present in the source block, absent from the destination, and absent from every other block moving in the same run. Report the tally over relocations, not strings (`Preservation: 16/16 relocations verified`). On any miss, restore **that** relocation from its snapshot, say which one lost content, and do **not** report the size reduction as a success.

**2. Re-measure.** Only once the probes pass:

```bash
wc -c ~/.claude/CLAUDE.md
```

Never claim a reduction from the projection alone. If the measured result grew, or is still over target, state it plainly and offer the next round - re-running the checklist over what remains, since the biggest lever usually moves once the file changes. Landing under target in one pass is not the expectation; converging over two or three is normal.
