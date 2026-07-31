# Verify after applying

Two things must be true when a run finishes: the file got smaller, and **nothing was lost on the
way**. Size is the easy half and the one that lies. A relocation is two writes - remove from the
source, append to the destination - and if the append fails while the removal succeeds, the size
check passes with flying colors. **Shrinking is the failure signature of data loss**, so byte count
alone can never be the proof.

Throughout this file, **source** is whichever file content is leaving (`~/.claude/CLAUDE.md`, a
project `./CLAUDE.md` under strict mode, or a note being consolidated away) and **destination** is
wherever it lands. The procedure is the same for all of them; only the paths change.

Run the checks below in order, every time changes are applied.

## 0. Back up every source, before touching anything

**Back up each file the run will remove content from** - not just the global CLAUDE.md. A move out of
a note (consolidation, splitting) and a strict-mode move out of `./CLAUDE.md` are just as
unrecoverable, and until this step existed they had no backup at all.

**Global-scope sources** are backed up in place, next to the file:

```sh
stamp=$(date +%Y%m%d-%H%M%S)
cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak.$stamp        # if it is a source this run
cp ~/.claude/notes/foo.md ~/.claude/notes/foo.md.bak.$stamp  # ditto, per source note
```

**Project-scope sources go outside the repo.** A strict run on `./CLAUDE.md` writes a
backup, and writing it beside the file drops an untracked artifact into the user's working
tree - one that most repos do not gitignore, and that on a public repo is an unwanted
tool-generated file. Send it to a project-keyed directory under `~/.claude/` instead:

```sh
enc=$(printf '%s' "$PWD" | sed 's#[/.]#-#g')
bk="$HOME/.claude/notation-backups/$enc"
mkdir -p "$bk"
cp ./CLAUDE.md "$bk/CLAUDE.md.bak.$stamp"
```

The encoding rule is stated once in `scope-resolution.md`; **inline it** as above rather
than calling a helper, because shell functions and variables do not survive from one Bash
invocation to the next. For the same reason, record the value of `$stamp` and substitute it
literally in any later invocation. Use the **same `$stamp`** for the whole run, across both
scopes, so the set restores together and there is no ambiguity about which snapshot to roll
back to. Never write a `.bak` into the repo working tree, and never delete a stray one you
find there - move it (see `audit-checklist.md` check 7).

**Back up before the first write, never after** - a snapshot of an already-edited file
restores the damage. This timing rule applies to both global-scope and project-scope
backups.

Destinations do not need a backup (they are appended to, not rewritten), but note the byte size of
each one now - check 2 uses it.

## 1. Classify each applied change

The probe only makes sense for content that moved **verbatim**. Sort every applied change into one
of two kinds and say which in the report:

- **Relocation** (tactics 1, 3, 4, 6, and the detail half of tactic 2): text leaves one file and
  lands in another unchanged. These get the full check below.
- **Compression** (tactics 5 and 7, and the surviving trigger line of tactic 2): text is *rewritten
  shorter in place*; nothing lands anywhere. A literal probe would fail these correctly-applied
  changes, so **do not probe them**. Instead state the standard they must meet - every distinct fact
  survives in the shorter text - and if a compression would drop a fact, it was never a legal
  compression; convert it to a relocation and move the fact into the note.

Mixing these up is the main way this check produces a false failure and then destroys good work with
an unnecessary restore.

## 2. Conservation check (the strong one)

For each relocation, a point probe proves an arbitrary interior line arrived - it cannot bound a
truncated tail. Byte conservation can. You already measured the block for its delta
(`size-budget.md` > "Every row's delta needs a method"), so:

```bash
wc -c ~/.claude/notes/gcloud.md   # destination, before and after
```

**The destination must grow by at least the byte count that left the source.** A shortfall means a
partial write - treat it exactly like a failed probe. Growth slightly above is normal (a blank line,
a dated heading); growth far below is the truncation the probe cannot see.

## 3. Preservation probe

### Pick the probes before applying

While the source text is still in front of you, choose **1 to 2 distinctive strings per relocation**:

- **Good probes:** an error message (`no matches found`), a sha (`e650897`), a flag
  (`--break-system-packages`), a path (`refs/pull/*/head`), a specific number (`738 asset files`),
  an API name (`getMaxMemoryCharacterCount`).
- **Bad probes:** a common word, a heading title, anything generic enough to already exist elsewhere.
- Prefer a string from the **middle** of the block, not its first line - a truncated write usually
  gets the first line right.
- **It must fit on one line.** `grep` is line-oriented, so a probe spanning a line break can never
  match and produces a guaranteed false failure.

**Every relocation contributes at least one probe.** The tally's denominator is the number of
relocations, not the number of strings, so an unprobed move can never hide in a clean-looking score.

### Assert the preconditions

A probe that cannot fail proves nothing. Before applying, confirm all three:

1. The probe **is** present in the source block being moved.
2. The probe is **not already** present in the destination file. If it is, either pick another
   string or record the baseline hit count and require the count to **increase** - and write the
   baseline down, because check 3's threshold reads it.
3. The probe does **not** appear in any *other* block being moved in the same run. Several
   relocations routinely land in the same note; if B's probe also occurs inside A's block, A's
   successful append satisfies B's check and B can be lost entirely while reporting verified.

### Check after applying

Use `/usr/bin/grep` explicitly and `-F` for a literal match - the bare `grep` in this environment is
a wrapper with ignore-file filtering that can return a silent zero, and probe strings routinely
contain regex metacharacters:

```bash
/usr/bin/grep -c -F 'getMaxMemoryCharacterCount' ~/.claude/notes/claude-code-internals.md
```

**Pass threshold:** hits `>= 1` for a fresh probe, or `>` the recorded baseline for a probe that
already existed in the destination. Check each probe against **its own destination file**, never the
whole tree - a tree-wide match tells you the string exists somewhere, which is exactly the question
you are not asking.

### Also check the source side

The inverse failure - destination append succeeded, source removal did not - passes every check
above and merely looks like an under-delivering projection, which the convergence rule below would
then excuse. One line closes it:

```bash
/usr/bin/grep -c -F 'getMaxMemoryCharacterCount' ~/.claude/CLAUDE.md   # must now be 0
```

A non-zero result means the move half-applied: the fact now lives in both tiers, which is the
cross-tier duplication check 5 exists to flag. Fix the removal rather than reporting a clean pass.

## 4. On failure: restore narrowly, and say what that costs

**A failed check fails the run.** Do not report a size reduction as a success alongside it.

**Restore only the failing relocation**, not the whole run: take that one block from the source's
`.bak` and re-insert it, then remove whatever partial text it wrote into the destination. This is
almost always the right move when 21 of 22 relocations succeeded.

**A full restore from the `.bak` is not free, and its cost must be stated if you do it.** The `.bak`
only covers sources. Restoring it returns *every* relocated block to the source file while the
successful appends **remain in their destinations** - so every good move becomes a cross-tier
duplicate (check 5), and any index line that was reverted leaves its note unindexed (check 2). If you
restore the whole run, you must also undo the destination appends, or say plainly that the notes tree
is now inconsistent and needs a follow-up pass.

Either way, name which relocation failed and which check caught it.

Deletions that are not relocations get the same treatment in reverse: check 5's cross-tier duplicate
removal is reported under `move` severity but writes nothing to a destination, so there is nothing to
probe. Instead prove the **surviving** copy still contains the fact *before* removing the duplicate.

## 5. Size re-measure and convergence

Only after checks 1-4 pass. Re-measure whichever file the run was budgeted against - the global file
always, plus `./CLAUDE.md` when the run was strict:

```bash
wc -c ~/.claude/CLAUDE.md
wc -c ./CLAUDE.md          # strict-mode runs only
```

Report the real before -> after -> target numbers. Never claim a reduction from the projection alone.

**Expect to converge over more than one pass.** The report's projection is an estimate (see
`size-budget.md` > "Projecting savings honestly"); the applied result frequently falls short because
replacement lines and index entries cost more than they look. That is normal. What is not normal, and
must never be waved through under this heading, is a shortfall that check 3's source-side assertion
would have explained - confirm the moves fully applied *before* attributing a gap to estimation.

If the measured size is still over target:

1. Say so plainly, with the measured number and the remaining gap.
2. Re-run the checklist over **what is left** - the file has changed, so the next-biggest lever has
   often changed too.
3. Offer the next round. Repeat until under target or until nothing can move without losing value,
   then report the best achievable size and name what is blocking the rest.

If the run ended net-positive on a file that has a no-growth rule, state that outright as a failed
run rather than burying it.
