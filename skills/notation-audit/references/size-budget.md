# CLAUDE.md size budget

Two different files are called CLAUDE.md and they get two different budgets. Throughout this skill,
**"the global file" always means `~/.claude/CLAUDE.md`** and **"a project CLAUDE.md" always means a
repo's own `./CLAUDE.md`**. Never apply one's rules to the other.

| File | Loads | Budget | Enforcement |
| --- | --- | --- | --- |
| `~/.claude/CLAUDE.md` | every prompt of **every** session, in every repo | 40,000 chars | **Strict** - net delta `<= 0` always, reduce until under target |
| `./CLAUDE.md` | only in the one repo it belongs to | soft, see below | **Advisory** by default; strict on request or recorded preference |

The asymmetry is the point. A line in the global file is paid for in every session you ever run. A
line in a project CLAUDE.md is paid for only while you are working in that repo, and is usually
earning its keep by orienting you in that codebase - build commands, architecture, team conventions.
**Growth there is normal and is not a defect.** Do not port the global file's scarcity mindset onto
a project file that is doing its job.

**The audit's job is to move the global file toward its budget - never away from it.** An audit run
that leaves `~/.claude/CLAUDE.md` larger than it found it has failed, even if every individual
finding was correct.

## The global budget (`~/.claude/CLAUDE.md`)

Claude Code warns when a single loaded memory file exceeds **roughly 5% of the model's context
window in characters, with a floor of ~40,000 chars** (`getMaxMemoryCharacterCount`). The floor is
the portable number - a file that fits under it fits on every model.

- **Hard ceiling:** `max(40000, 5% of the context window)` chars - above this the harness warns.
- **Target:** **<= 40,000 chars**, and comfortably under it if the file is already close, so
  ordinary growth from `/notation:notate` does not immediately trip the ceiling.
- **Green band:** <= 32,000 chars (80% of the floor). A file in the green band only needs the
  no-growth rule below, not an active reduction pass.

Measure, never estimate:

```bash
wc -c ~/.claude/CLAUDE.md
awk '/^## Topical Notes Index/,0' ~/.claude/CLAUDE.md | wc -c   # how much is index
```

## The two rules (global file only)

1. **No-growth rule (always).** The net character delta of an audit's applied changes must be
   `<= 0`. This binds even when the file is already under budget.
2. **Reduction rule (when over the target).** If the file is over 40,000 chars, the audit must
   propose enough relocation to land under it - or, if that is not achievable without losing value,
   say so explicitly and report the best achievable size plus what is blocking the rest.

Neither rule applies to a project `./CLAUDE.md`. See the next section.

**Preservation still wins over both.** These rules are satisfied by **relocating** facts into
`~/.claude/notes/`, never by deleting still-true content. If the only way to hit the budget would be
to destroy a fact, miss the budget and say why. See `routing-rubric.md` > "Preservation".

## Project CLAUDE.md (`./CLAUDE.md`)

A project file only costs context inside its own repo, so it gets **headroom, not a leash**. There
is no no-growth rule and no reduction rule by default.

Three bands, measured with `wc -c ./CLAUDE.md`:

- **Under 20,000 chars - silent.** Normal and healthy. Do not report a size, do not propose a
  trim, do not mention it. Most project files live here forever.
- **20,000 to 40,000 - one advisory line, no findings.** Report the number in the ledger and move
  on: `./CLAUDE.md: 24,180 chars (soft cap 40,000) - fine, no action`. Do not manufacture move
  findings. Growing into this band is expected for a large or long-lived codebase.
- **Over 40,000 - a real finding, severity `move`.** This is the harness's own per-file warning
  threshold, so the file now costs a warning and a meaningful slice of every session in that repo.
  Propose relocation into **project-local homes** (below) using the project-file tactics in
  "Reduction tactics", and report a projected size. It is still advisory: the user may decline and
  the audit accepts that without re-raising it.

**Where project detail goes when it does need to move** - never to `~/.claude/notes/`, which is
global and would pollute every other repo:

1. `./.claude/docs/<name>.md` - the project's own long-form guides, specs, phase write-ups. This is
   the main destination, the project-tier equivalent of a topical note.
2. Existing repo docs - `README.md`, `CONTRIBUTING.md`, `docs/`. A build or setup section often
   belongs in the repo's real documentation, not in an agent-facing file.
3. Project memory (`~/.claude/projects/<encoded-cwd>/memory/`) for a fact that is about the work
   rather than a convention the team needs.

Leave a one-line pointer in `./CLAUDE.md` for anything relocated, exactly as the global file does.

### Strict mode for a project file

Enforce the global file's rules (net delta `<= 0`, reduce until under target) on a project
`./CLAUDE.md` **only** when one of these is true, in precedence order:

1. **The user asks in this run** - "audit this repo strictly", "enforce the budget on the project
   CLAUDE.md", "strict". An explicit ask always wins and applies to this run only.
2. **A recorded project preference** - a `project`-type memory file for this repo stating that its
   CLAUDE.md is budgeted, optionally with its own target. Check the project's `MEMORY.md` while
   reading it in step 1. Offer to record one when the user asks for strict mode, so the next
   session inherits it.
3. **Otherwise: advisory.** The three bands above.

When strict mode is on, say so in the scorecard so it is never ambiguous which rules produced the
findings, and name which trigger fired: `strict (requested)` for #1, `strict (project memory)` for
#2. A target the user names beats the 40,000 default.

**Strict mode overrides the three bands, including the silent one.** A strict run always prints the
project ledger line and always scores the file, even under 20,000 chars - the whole point of asking
for strict is to see the number. Under strict, the file's own target is the named one (or 40,000),
the net delta must be `<= 0`, and findings are real rather than advisory. Relocation still goes to
project-local homes only; strict changes the *enforcement*, never the *destination*.

## Additive findings must be offset (global file)

Several audit checks *add* characters to `~/.claude/CLAUDE.md`:

- adding an index line for an unindexed note (check 2),
- restoring a description on a stale index entry (check 2),
- any newly promoted global rule.

Each of these is legitimate, but each must be **counted as a positive delta in the ledger** and
covered by relocation elsewhere in the same run. Never present an additive-only audit for a global
file that is at or over budget: pair it with at least one move that more than pays for it.

(Recency-date findings, check 6, never touch the global file - inline rules are not dated.)

## The size ledger

Every audit report carries a ledger, and every proposed row carries its own signed character delta
against the file it touches (`-1,840`, `+118`, `0`). Compute the deltas from the actual diff text,
not by feel.

**Deltas are per-file and never pooled.** A row's delta belongs to exactly one file, and the three
buckets total separately: `global` (`~/.claude/CLAUDE.md`), `notes` (`~/.claude/notes/<topic>.md`),
and `project` (`./CLAUDE.md`, `./.claude/docs/`, a project memory file). Only global-file deltas
feed the global ledger, the no-growth rule, and the pre-apply gate; a `notes` row and a `project`
row each feed their own ledger line alone. When a report contains rows of more than one kind, say
which file each delta is against (see `output-format.md` > Zone 2) so a note or project move can
never be read as a global reduction.

```
~/.claude/CLAUDE.md: 59,482 chars (over the 40,000 target by 19,482)
Proposed:            -21,310 chars -> 38,172 projected (under target)
```

Add a **notes line** whenever any row's `file` is `notes` - a check 9 note shrink, a consolidation,
a split. It is global-scope but never gated, so it gets its own line and never merges into the
figures above:

```
~/.claude/notes/:    -3,140 chars across 2 notes (global scope, not gated)
```

Do the same for `project` rows that touch no `./CLAUDE.md` - a project memory file a check 9 move
grows, for instance. That delta belongs on its own line too, so it is never dropped from the report
for want of somewhere to put it:

```
project memory:      +2,980 chars (project scope, not gated)
```

Add a project line **only when the current project has its own `./CLAUDE.md`**, and only when it is
at 20,000 chars or more - below that it stays silent, unless strict mode is on (a strict run always
prints the line, at any size):

```
./CLAUDE.md:         24,180 chars (soft cap 40,000) - fine, no action
```

Never sum these lines into one figure. `global`, `notes` and `project` are separate budgets with
separate rules - only the first is gated - and a combined number would imply a project file, or a
note, can be "paid for" by shrinking the global one, or that a note shrink counts as an
every-session-file reduction.

If a projected number is still over target, state that plainly and name the next-best lever rather
than quietly stopping.

## Reduction tactics, best first (global file)

Every tactic below is lossless at the fact level - the information survives, it just stops being
loaded every session.

**These nine tactics are for `~/.claude/CLAUDE.md` only.** All but tactic 9 move content into
`~/.claude/notes/` and the Topical Notes Index; tactic 9 moves it into a skill. Both destinations
are global - applying either to a project file would leak one repo's specifics into every other
session. For a project file, use the project-file tactics at the end of this section instead.

1. **Subsection -> note.** A whole `##`/`###` subsection about one tool, platform, API, SDK, or
   service moves verbatim into `~/.claude/notes/<topic>.md`, replaced by one index line. Biggest
   single win; usually thousands of chars each.
2. **Fat inline entry -> note + pointer.** A multi-line inline bullet with commands, error strings,
   or a recipe becomes a note section plus a one-line inline pointer (keep the *trigger* inline, move
   the *detail* out): `` `- <one-line rule>. Detail: `notes/<topic>.md`` ``.
3. **Append into an existing note.** Prefer appending to a topic note that already exists over
   creating a new one - a new note also costs a new index line. Check `~/.claude/notes/` first.
   **Only when that note is genuinely the right topical home**: if a future session searching
   for this fact would not open that file, mint the new note and offset the index line
   elsewhere in the run. See "When two rules conflict" below.
   <!-- precedence-ref: routing-vs-index-cost -->
4. **Cross-tier duplicate removal.** An inline copy of a fact that already lives in a note is the
   one safe deletion (check 5). Confirm the note's copy is at least as complete first; merge any
   inline-only detail INTO the note before dropping the inline copy.
5. **Index-line compression.** Index hooks route, they do not teach. Cap each at ~100 chars: enough
   to know when to open the note, no more. In a mature setup the index can be a third or more of the
   whole file, so this is often the second-biggest lever after subsection moves. Compute it against
   the lines tactic 8 has already compressed, never against the raw ones.
   <!-- precedence-ref: encoding-vs-cap -->
6. **Note consolidation.** Several thin sibling notes on one subject merge into a single topic note,
   removing N-1 index lines along with the duplication.
7. **Prose -> one line.** Collapse a paragraph into the `` `pattern` - note `` inline format, but
   **only** when every distinct fact survives; if the paragraph holds two facts, it becomes two
   lines or moves to a note. Never summarize away a fact to save bytes.
8. **Index encoding cost.** Drop the markdown-link syntax from the Topical Notes Index -
   `- [name](notes/name.md) - hook` becomes `- name - hook`, with the convention stated once above
   the index. Removes waste rather than moving a fact, so it needs no destination and is the first
   index lever to reach for. Do not run it in the same report as tactic 5 without excluding the
   overlap - see "When two rules conflict".
   <!-- precedence-ref: encoding-vs-cap -->
9. **Section -> skill.** An inline section that is a *procedure* - ordered steps where skipping one
   breaks the outcome - moves into `~/.claude/skills/<name>/SKILL.md`, leaving the trigger inline.
   Unlike tactic 1 it costs **no index line**, because skills are discovered by their own frontmatter
   rather than through the Topical Notes Index, which makes it the cheapest large move available.
   Routing is `routing-rubric.md` rule 3; the procedure-vs-tool-surface tie-break lives there.
   <!-- precedence-ref: procedure-vs-surface -->

Do NOT reach for: deleting still-true rules, dropping the genuinely global sections (permissions,
gh/git, shell/PATH, session/harness, workflow, accessibility), or condensing two facts into one.

## When two rules conflict

Several rules in this skill pull against each other by design. Each pairing below states which
wins, so the answer is never a session's judgment call - two sessions reaching opposite
conclusions from the same checklist is the failure this section exists to prevent. Every rule
that participates in one of these carries a pointer back here.

**The question that settles all of them: does this index line buy findability, or only
tidiness?** An index line is the one currency the budget protects - it costs context in every
session, in every repo, forever. Note bytes cost nothing until a note is opened. So an index
line is worth minting when it is what lets a future session *find* a fact, and is not worth
minting to make an already-findable set of facts tidier.

<!-- precedence-def: routing-vs-index-cost -->
**Routing quality beats index-line cost.** Tactic 3 prefers appending to an existing note over
minting a new one, because a new note costs an index line. That is sound budget advice and bad
routing advice when no existing note actually fits. Apply the test: **would a future session
looking for this fact open THIS file?** If no, the note is the wrong home no matter what it
saves. A fact filed where nobody will look is barely better than a deleted one - and it passes
every check this skill runs, including the preservation probe, because the string *is* on disk.
Mint the new note and offset its index line elsewhere in the same run. ~110 chars never
outranks whether the fact can be found again. Real case: the no-fancy-dashes *rationale*
appended to `notes/unicode-bulk-edit.md`, a note about perl mechanics - correct on cost,
unfindable for anyone searching why em-dashes are banned.

<!-- precedence-def: encoding-vs-cap -->
**Tactic 8 is measured first and tactic 5 gets the remainder.** Both act on the same index lines
and both count the same bytes: tactic 5's method is `-(sum of current lengths of the over-cap
lines) + (cap x count)`, and "current length" includes the ~34 chars of link syntax tactic 8
claims on its own. A line like `- [very-long-name](notes/very-long-name.md) - <120-char hook>`
appears in both rows, so a report carrying both over-states the saving - and the `global` bucket
feeds the no-growth gate and the projected-size line, which makes that an inflated promise, not a
rounding error. Run tactic 8 first, because it is exact and needs no destination, then compute
tactic 5 **against the compressed lines**: `-(sum of compressed lengths of the still-over-cap
lines) + (cap x count)`. Compressing usually pulls some lines back under the cap on its own, so
tactic 5's count shrinks too. If you report only one of them, say which - a tactic 5 figure taken
from uncompressed lines is an estimate that leans high, and `output-format.md` requires that to
be marked.

<!-- precedence-def: split-vs-budget -->
**The budget beats splitting an oversized note.** Check 3 flags a large note for splitting by
sub-topic; each split adds an index line. Unlike the case above, a split buys no findability -
those facts are already correctly filed and already reachable through the existing index line.
It buys tidiness, paid for in the every-session currency. So while `~/.claude/CLAUDE.md` is at
or over target, **note splits are deferred**, and the audit says it is deferring them rather
than staying silent. Note size is not itself a problem: notes load on demand, so a 50 KB note
costs nothing until something opens it. If a split is done anyway, its new index lines are a
positive delta in the ledger like any other and must be offset in the same run. Real case: an
applied run landed at 39,887 chars, 113 under target, with two notes flagged as split
candidates - doing both would have added roughly 220 to 440 chars and undone the reduction the
same audit had just made, with every individual finding still looking correct.

The mirror case is always welcome and needs no deferral: **merging** thin sibling notes
(tactic 6) removes N-1 index lines, buying back the exact currency the two rules above are
arguing over.

### Project-file tactics

Same shape, project-local destinations. Preservation applies identically - relocate, never trim.

1. **Subsection -> `./.claude/docs/<name>.md`.** A long-form guide, spec, or phase write-up moves
   out verbatim, replaced by a one-line pointer in `./CLAUDE.md`. The main lever.
2. **Section -> the repo's real docs.** Build, setup, and contribution steps usually belong in
   `README.md` / `CONTRIBUTING.md` / `docs/`, which humans read too. Point at them rather than
   duplicating.
3. **Work-specific fact -> project memory.** A fact about the current work rather than a team
   convention belongs in `~/.claude/projects/<encoded-cwd>/memory/`, indexed by `MEMORY.md`.
4. **Prose -> one line**, under the same rule as tactic 7 above: only when every distinct fact
   survives.

There is no project-tier equivalent of the Topical Notes Index, so a project relocation costs no
index line - the one-line pointer in `./CLAUDE.md` is the whole overhead.

## Projecting savings honestly

Quote a saving from the **distribution, not the total**. Before promising "compressing the index
saves ~12k", measure the per-line spread - median length and how many lines actually exceed the
budget - because a total says nothing about how much of it is compressible.

### Every row's delta needs a method, not a feeling

`output-format.md` requires a signed delta per row, "computed from the diff text" - but at report
time the diff does not exist yet. Produce the number by **measuring what you can and drafting the
rest**, per tactic:

| Tactic | Method |
| --- | --- |
| 1. Subsection -> note | `delta = -(measured bytes of the lines leaving) + (drafted pointer line) + (drafted index line, only if the note is new)`. All parts are available now: the section is in front of you, and both lines are ones you write at report time. |
| 2. Fat inline entry -> note + pointer | Same three parts as tactic 1: `-(measured bytes of the entry) + (drafted pointer) + (drafted index line if the note is new)`. **Draft the replacement before quoting the number** - it is the substance of the proposal anyway. |
| 3. Append into an existing note | Same as tactic 1 **minus the index line**, since the note is already indexed: `-(measured bytes leaving) + (drafted pointer)`. Not `0` - that is the capture-side answer, where nothing leaves the file. |
| 4. Cross-tier duplicate removal | `-(measured bytes of the inline copy)`. Exact - nothing replaces it. |
| 5. Index-line compression | Measure the per-line spread, then `delta = -(sum of current lengths of the over-cap lines) + (cap x count)`. |
| 6. Note consolidation | `-(measured bytes of the N-1 index lines being dropped)`. Exact. |
| 7. Prose -> one line | Draft the replacement line, then `-(measured) + (drafted)`. Never quote this one without drafting. |
| 8. Index encoding cost | Run the transform and diff the totals (`audit-checklist.md` check 2): `delta = -(saved)`. Exact and measured by construction - the compressor counts both sides, so never estimate it. If tactic 5 also appears in the report, subtract the overlap first. |
| 9. Section -> skill | `-(measured bytes of the lines leaving) + (drafted inline trigger line)`. **No index line**, in either direction: a skill is not indexed, so tactic 1's third term does not apply. The row's `file` label is `skill`, and the SKILL.md bytes total on their own ledger line, never in `global`. |

The pattern is the same throughout: **the thing being removed is always measurable, so measure it;
the thing replacing it is always short, so draft it.** A delta quoted without doing both is a guess.

**"Measured" means a byte count you ran, not a block you eyeballed.** Extract the lines and count
them - do not estimate from how long the section looks in context:

```bash
sed -n '412,468p' ~/.claude/CLAUDE.md | wc -c
```

### Mark which rows are measured

A row is **measured** only when *both* halves are real: the removed bytes were counted with a
command, and the replacement line was drafted. Tactics 4, 6 and 8 have no replacement, so they are
always measured - tactic 8 counts both sides itself. Tactics 1, 2, 3, 7 and 9 are measured once you
draft. A row is **estimated** when the replacement length is assumed rather than drafted - tactic
5's cap is the standard case. Mark the estimated ones - see `output-format.md` > Zone 2 - so a
reader knows which figures to trust.

Note the direction each estimate errs in, and do not describe them as if they all lean one way:
**tactic 5 is pessimistic** (the cap is a ceiling, so a real compression usually saves a little more
than quoted), while an **undrafted replacement is optimistic** (drafted lines reliably run longer
than imagined). The net-optimistic bias below comes from the undrafted rows and from index lines
that get forgotten, which is exactly why the table above counts them explicitly.

### A projection is a projection

State plainly that the ledger's projected size is an estimate and that the apply step may need
another round. In aggregate these projections skew **optimistic** - undrafted replacement lines and
forgotten index entries cost more than they look - so a run projected to land just under target
frequently lands just over. Never excuse a shortfall as estimation error before confirming the moves
actually applied in full (`verify-after-apply.md` > "Also check the source side"); a half-applied
move looks identical to an optimistic estimate. When
the projection is within a few thousand chars of the target, say so ("projected 38,172 - close
enough to target that a second pass may be needed").

After applying, restate the **measured** number rather than letting the projection stand, and
converge over further passes as needed. Full procedure: `verify-after-apply.md`.

## Verify after applying

Two checks, in order: **prove nothing was lost**, then re-measure. Size alone cannot be the proof -
a relocation whose destination write failed makes the file smaller, so shrinking is also the failure
signature of data loss. Full procedure, probe selection, and the restore-on-failure rule:
`verify-after-apply.md`.
