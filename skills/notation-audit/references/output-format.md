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

## Zone 2 - Per-tier tables

One compact table per non-empty tier (or per severity group, for audit). Order rows
high-confidence first (capture) or move -> fix -> tidy (audit). Number rows continuously across
all tier tables (do not reset to 1 per tier) so the picker and the diffs below can reference
them by a unique `#`.

Capture columns: `#`, `title`, `kind`, `conf`, `destination`.
Audit columns: `#`, `title`, `severity`, `problem`.

Capture example:

    GLOBAL RULES
      #  title               kind   conf   destination
      1  gh merge wildcard    NEW    high   ~/.claude/CLAUDE.md

    TOPICAL NOTES
      #  title               kind   conf   destination
      2  railway bucket TTL   NEW    high   ~/.claude/notes/railway.md
      3  supabase RLS gotcha  NEW    med    ~/.claude/notes/supabase.md

Audit example:

    MOVE
      #  title                    severity   problem
      1  gcloud subsection        move       tool-specific, belongs in notes/gcloud.md

## Zone 3 - Diffs below

After all tables, print the full diffs, each keyed by the same `#` used in the table. Put the
destination-path header on its own line, then the diff body in a fenced block tagged `diff` so
`+`/`-` lines render with color coding. This keeps tables scannable while still printing every
diff above any AskUserQuestion picker (the picker has no preview pane, so diffs must be visible
first).

For a `NEW` proposal, show only the added (`+`) lines. For an `UPDATE`, show both the removed
(`-`) and added (`+`) lines so it renders as a real before/after diff rather than just an
addition.

[1] ~/.claude/CLAUDE.md  (GLOBAL RULES)

```diff
+ `gh pr merge * --repo <o>/<r>:*` - narrow per-repo merge permission rule shape
```

## Cosmetic rules (apply to all modes)

- Plain hyphens (`-`) only. No em-dashes or en-dashes.
- Reference files by absolute path.
- Be concise. Tables over prose.
- Diff bodies go in ` ```diff ` fenced blocks so `+`/`-` lines get color coding.
