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

**Deltas are per-file and never pooled.** A row's delta belongs to exactly one file, and the two
files' deltas total separately. Only global-file deltas feed the global ledger, the no-growth rule,
and the pre-apply gate; a project-file row's delta feeds the project line alone. When a report
contains rows of both kinds, say which file each delta is against (see `output-format.md` > Zone 2)
so a project move can never be read as a global reduction.

```
~/.claude/CLAUDE.md: 59,482 chars (over the 40,000 target by 19,482)
Proposed:            -21,310 chars -> 38,172 projected (under target)
```

Add a second line **only when the current project has its own `./CLAUDE.md`**, and only when it is
at 20,000 chars or more - below that it stays silent, unless strict mode is on (a strict run always
prints the line, at any size):

```
./CLAUDE.md:         24,180 chars (soft cap 40,000) - fine, no action
```

Never sum the two files into one figure. They are separate budgets with separate rules, and a
combined number would imply a project file can be "paid for" by shrinking the global one.

If a projected number is still over target, state that plainly and name the next-best lever rather
than quietly stopping.

## Reduction tactics, best first (global file)

Every tactic below is lossless at the fact level - the information survives, it just stops being
loaded every session.

**These seven tactics are for `~/.claude/CLAUDE.md` only.** They all move content into
`~/.claude/notes/` and the Topical Notes Index, which are global - applying them to a project file
would leak one repo's specifics into every other session. For a project file, use the project-file
tactics at the end of this section instead.

1. **Subsection -> note.** A whole `##`/`###` subsection about one tool, platform, API, SDK, or
   service moves verbatim into `~/.claude/notes/<topic>.md`, replaced by one index line. Biggest
   single win; usually thousands of chars each.
2. **Fat inline entry -> note + pointer.** A multi-line inline bullet with commands, error strings,
   or a recipe becomes a note section plus a one-line inline pointer (keep the *trigger* inline, move
   the *detail* out): `` `- <one-line rule>. Detail: `notes/<topic>.md`` ``.
3. **Append into an existing note.** Prefer appending to a topic note that already exists over
   creating a new one - a new note also costs a new index line. Check `~/.claude/notes/` first.
4. **Cross-tier duplicate removal.** An inline copy of a fact that already lives in a note is the
   one safe deletion (check 5). Confirm the note's copy is at least as complete first; merge any
   inline-only detail INTO the note before dropping the inline copy.
5. **Index-line compression.** Index hooks route, they do not teach. Cap each at ~100 chars: enough
   to know when to open the note, no more. In a mature setup the index can be a third or more of the
   whole file, so this is often the second-biggest lever after subsection moves.
6. **Note consolidation.** Several thin sibling notes on one subject merge into a single topic note,
   removing N-1 index lines along with the duplication.
7. **Prose -> one line.** Collapse a paragraph into the `` `pattern` - note `` inline format, but
   **only** when every distinct fact survives; if the paragraph holds two facts, it becomes two
   lines or moves to a note. Never summarize away a fact to save bytes.

Do NOT reach for: deleting still-true rules, dropping the genuinely global sections (permissions,
gh/git, shell/PATH, session/harness, workflow, accessibility), or condensing two facts into one.

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
budget - because a total says nothing about how much of it is compressible. After applying, restate
the **measured** number rather than letting the projection stand.

## Verify after applying

Re-measure and report before -> after -> target. Do not claim a reduction you have not measured:

```bash
wc -c ~/.claude/CLAUDE.md
```

Report the real numbers, and if the run ended net-positive or still over target, say so outright
and offer the next round.
