# Notation output format

Shared presentation format for `/notation:notate`, `/notation:notate-all`, and the
`notation-audit` skill. Render every proposal list and audit report in the three zones below
so output is identical across modes.

## Zone 1 - Scorecard header

One or two lines. State the session read (or audit scope) and the tally, using ` - ` as the
separator and `->` for routing.

- Capture: `Read: <session-type> session (<N> turns) - <M> learnings -> <a> global - <b> notes - <c> memory`
- Audit:   `Audited: CLAUDE.md + <N> notes + <M> memories - <x> move - <y> fix - <z> tidy`

If a tier has zero items, omit it from the tally rather than printing `0`.

**The size ledger.** `~/.claude/CLAUDE.md` is budgeted at <= 40,000 chars (see `size-budget.md`).
Print the ledger directly under the scorecard - **always** for an audit, and for a capture run
**whenever any proposal touches that file** (an inline rule or a new index line). Measured with
`wc -c`, never estimated.

    Audit:   ~/.claude/CLAUDE.md: 59,482 chars (over the 40,000 target by 19,482)
             Proposed:            -21,310 chars -> 38,172 projected (under target, estimate)

    Capture: ~/.claude/CLAUDE.md: 38,140 chars -> +214 -> 38,354 projected (target 40,000)

A project `./CLAUDE.md` gets its own line, never folded into the global figure, and only when the
file exists AND is at 20,000 chars or more (below that it stays silent - that is the normal, healthy
state and reporting it just adds noise):

    ./CLAUDE.md:         24,180 chars (soft cap 40,000) - fine, no action

Under strict mode the line is **always** printed, at any size, and carries the trigger instead of
the soft-cap note - `strict (requested)` when the user asked this run, `strict (project memory)`
when a recorded preference supplied it - so it is never ambiguous which rules produced the project
findings.

    ./CLAUDE.md:         12,040 chars (strict (requested), target 40,000) -> -1,200 -> 10,840

If the projection is over target, append ` - still over, next lever: <x>` (audit) or
` - consider /notation:notate's budget gate, or run notation-audit` (capture) rather than letting
the number pass without comment.

**A projected line is an estimate and must read as one.** Say `projected`, never a bare figure that
could pass for a measurement, and when the projection lands within a few thousand chars of target,
add that a second pass may be needed - estimates here skew optimistic. See `size-budget.md` >
"A projection is a projection".

After applying, print the ledger again with the **re-measured** after-size - never claim a size you
have not measured - and print the preservation tally on its own line above it:

    Preservation: 16/16 relocations verified (bytes conserved, probes hit, sources clean).
    ~/.claude/CLAUDE.md: 59,482 -> 39,887 chars (target 40,000) - under, after 4 passes

If any probe failed, that line replaces the size line entirely: name the move that lost content,
state that the file was restored from the backup, and do not present a reduction as a result.

## Zone 2 - Per-tier tables

One compact table per non-empty tier (or per severity group, for audit). Order rows
high-confidence first (capture) or move -> fix -> tidy (audit). Number rows continuously across
all tier tables (do not reset to 1 per tier) so the picker and the diffs below can reference
them by a unique `#`.

Capture columns: `#`, `title`, `kind`, `conf`, `destination`, and `delta` when the table needs it.
Audit columns: `#`, `title`, `severity`, `problem`, `delta`.

`delta` is that row's signed effect in characters on **the file that row touches** (`-1,840`,
`+118`, `0`). Audit tables always carry it. Compute it by measuring the content being removed and
**drafting** the line replacing it - never by feel; the per-tactic methods are in `size-budget.md` >
"Every row's delta needs a method". Mark a row whose replacement length was assumed rather than
drafted with a trailing `~` (`-3,610~`), so an estimated figure is never read as a measured one.

**Deltas never pool across the two CLAUDE.md files.** A global-file row's delta and a project-file
row's delta are different currencies: only the global ones sum to the global ledger's net figure and
feed the pre-apply gate. When a report contains any project-file row, add a `file` column to that
table (values `global` / `project`) and total the two groups separately in the ledger. A report with
only global rows omits the column. **A capture table carries it when ANY of
its rows touches that file** - every inline global rule, and every note row that also adds a Topical
Notes Index line. Delta is a whole-column decision, never per-row: once a table has the column,
every row in it shows a number, and rows with no CLAUDE.md effect show `0`. A table where no row
touches either file omits the column entirely. Across the whole report the global-file deltas sum to
the global ledger's net figure.

Capture example (GLOBAL RULES always carries delta; TOPICAL NOTES carries it here because row 2
creates a note and therefore an index line, while row 3 appends to a note that is already indexed):

    GLOBAL RULES
      #  title               kind   conf   destination           delta
      1  gh merge wildcard    NEW    high   ~/.claude/CLAUDE.md    +94

    TOPICAL NOTES
      #  title               kind   conf   destination                  delta
      2  railway bucket TTL   NEW    high   ~/.claude/notes/railway.md   +118
      3  supabase RLS gotcha  NEW    med    ~/.claude/notes/supabase.md     0

Audit example (row 1 drafted its replacement pointer, so both halves are measured; row 2 assumes the
~100-char cap as the replacement length, so it carries the `~` estimate marker):

    MOVE
      #  title                    severity   problem                                    delta
      1  gcloud subsection        move       tool-specific, belongs in notes/gcloud.md   -1,840
      2  index hooks over 100ch   move       31 lines teach instead of route             -3,610~

    FIX
      #  title                    severity   problem                                    delta
      3  pytest.md unindexed      fix        note exists with no index line              +112

## Zone 3 - Diffs below

After all tables, print the full diffs, each keyed by the same `#` used in the table. Put the
destination-path header on its own line, then the diff body in a fenced block tagged `diff` so
`+`/`-` lines render with color coding. This keeps tables scannable while still printing every
diff above any AskUserQuestion picker (the picker has no preview pane, so diffs must be visible
first).

For a `NEW` proposal, show only the added (`+`) lines. For an `UPDATE`, show both the removed
(`-`) and added (`+`) lines so it renders as a real before/after diff rather than just an
addition.

**Removals (`-` lines) are the exception, not the norm.** Most notation is additive - append
new lines, relocate detail to notes, keep existing content. An `UPDATE` should carry `-` lines
only when the removed content is factually wrong or directly contradicted by the new learning
(see `routing-rubric.md` > "Preservation"). When a diff does delete a line, its table `problem`
/ `why` must state why the old line is gone ("removes X - contradicted by Y"), so no deletion
is silent. A `move` that relocates CLAUDE.md content into a note shows the `-` lines leaving
CLAUDE.md AND the identical `+` lines landing in the note - the fact is preserved, not dropped.

[1] ~/.claude/CLAUDE.md  (GLOBAL RULES)

```diff
+ `gh pr merge * --repo <o>/<r>:*` - narrow per-repo merge permission rule shape
```

## Cosmetic rules (apply to all modes)

- Plain hyphens (`-`) only. No em-dashes or en-dashes.
- Reference files by absolute path.
- Be concise. Tables over prose.
- Diff bodies go in ` ```diff ` fenced blocks so `+`/`-` lines get color coding.
