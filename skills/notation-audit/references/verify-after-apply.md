# Verify after applying

Two things must be true when an audit finishes: the file got smaller, and **nothing was lost on the
way**. Size is the easy half and the one that lies. A relocation is two writes - remove from the
source, append to the destination - and if the append silently fails while the removal succeeds, the
size check passes with flying colors. **Shrinking is the failure signature of data loss**, so byte
count alone can never be the proof.

Run both checks below, in this order, every time findings are applied.

## 1. Preservation probe (run first - it can fail the run)

For every applied **move**, prove the moved text is now in its destination.

### Pick the probes before applying

While you still have the source text in front of you, choose **1 to 2 distinctive strings** per move
from the content being relocated:

- **Good probes:** an error message (`no matches found`), a sha (`e650897`), a flag
  (`--break-system-packages`), a path (`refs/pull/*/head`), a specific number (`738 asset files`),
  an API name (`getMaxMemoryCharacterCount`).
- **Bad probes:** a common word, a heading title, anything generic enough to already exist elsewhere
  in the notes tree. A probe that matches for the wrong reason is worse than no probe.
- Prefer a string from the **middle** of the moved block, not its first line. A truncated write often
  gets the first line right.

Record each probe with the destination file it must land in.

### Assert the preconditions

A probe that cannot fail proves nothing. Before applying, confirm both:

1. The probe **is** present in the source text being moved (`1` or more hits). If it is not, the
   probe is wrong - pick another.
2. The probe is **not already** present in the destination file (`0` hits). If it is, the post-apply
   check would pass without the move ever happening. Pick a different string, or count hits before
   and require the count to increase.

### Check after applying

Use `/usr/bin/grep` explicitly and `-F` for a literal match - the bare `grep` in this environment is
a wrapper with ignore-file filtering that can return a silent zero, and probe strings routinely
contain regex metacharacters:

```bash
/usr/bin/grep -c -F 'getMaxMemoryCharacterCount' ~/.claude/notes/claude-code-internals.md
```

Check each probe against **its own destination file**, never against the whole tree - a tree-wide
match tells you the string exists somewhere, which is exactly the question you are not asking.

### Report it, and fail loudly

- Report the tally explicitly, as its own line: `Preservation: 22/22 relocated phrases verified in
  their destination.`
- **If any probe fails, the run failed.** Restore from the backup
  (`cp ~/.claude/CLAUDE.md.bak.<stamp> ~/.claude/CLAUDE.md`), say which move lost content and which
  probe missed, and do **not** report the size reduction as a success. A smaller file with a missing
  fact is the worst outcome this skill can produce.
- Never report a size win and a failed probe in the same breath as though they offset.

Deletions that are not moves (a redundant cross-tier copy, check 5) get the same treatment in
reverse: prove the surviving copy still contains the fact **before** removing the duplicate.

## 2. Size re-measure and convergence

Only after the probes pass:

```bash
wc -c ~/.claude/CLAUDE.md
```

Report the real before -> after -> target numbers. Never claim a reduction from the projection alone.

**Expect to converge over more than one pass.** The report's projection is an estimate (see
`size-budget.md` > "Projecting savings honestly"); the applied result is usually smaller than
promised because replacement lines and index entries cost more than they look. This is normal and
not a defect - what is a defect is presenting the first pass as final when it did not land.

If the measured size is still over target:

1. Say so plainly, with the measured number and the remaining gap.
2. Re-run the checklist over **what is left** - the file has changed, so the next-biggest lever has
   often changed too.
3. Offer the next round. Repeat until under target or until nothing can move without losing value,
   then report the best achievable size and name what is blocking the rest.

If the run ended net-positive on the global file, state that outright as a failed run rather than
burying it.
