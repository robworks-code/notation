# CLAUDE.md size budget

`~/.claude/CLAUDE.md` loads into **every** prompt of **every** session. Its size is a recurring
tax, so the audit treats it as a budgeted resource, not just a tidiness concern.

**The audit's job is to move the global file toward the budget - never away from it.** An audit run
that leaves `~/.claude/CLAUDE.md` larger than it found it has failed, even if every individual
finding was correct.

## The budget

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

## The two rules

1. **No-growth rule (always).** The net character delta of an audit's applied changes must be
   `<= 0`. This binds even when the file is already under budget.
2. **Reduction rule (when over the target).** If the file is over 40,000 chars, the audit must
   propose enough relocation to land under it - or, if that is not achievable without losing value,
   say so explicitly and report the best achievable size plus what is blocking the rest.

**Preservation still wins over both.** These rules are satisfied by **relocating** facts into
`~/.claude/notes/`, never by deleting still-true content. If the only way to hit the budget would be
to destroy a fact, miss the budget and say why. See `routing-rubric.md` > "Preservation".

## Additive findings must be offset

Several audit checks *add* characters to CLAUDE.md:

- adding an index line for an unindexed note (check 2),
- restoring a description on a stale index entry (check 2),
- any newly promoted global rule.

Each of these is legitimate, but each must be **counted as a positive delta in the ledger** and
covered by relocation elsewhere in the same run. Never present an additive-only audit for a file
that is at or over budget: pair it with at least one move that more than pays for it.

(Recency-date findings, check 6, never touch CLAUDE.md - inline rules are not dated.)

## The size ledger

Every audit report carries a ledger, and every proposed row carries its own signed CLAUDE.md delta
in chars (`-1,840`, `+118`, `0`). Compute the deltas from the actual diff text, not by feel.

```
CLAUDE.md: 59,482 chars (over the 40,000 target by 19,482)
Proposed:  -21,310 chars -> 38,172 projected (under target)
```

If the projected number is still over target, state that plainly and name the next-best lever
rather than quietly stopping.

## Reduction tactics, best first

Every tactic below is lossless at the fact level - the information survives, it just stops being
loaded every session.

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
