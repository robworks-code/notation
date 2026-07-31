# Scope resolution

Which files a piece of notation may touch, and how to find them. Used by
`/notation:notate` when capturing and by `notation-audit` when auditing.

## Location does not tell you scope

Scope is defined by the **load condition** - which sessions pay for the content - not by
where the file sits on disk. This trips people because project memory lives *under*
`~/.claude/` yet is project-scoped, while `~/.claude/notes/` sits beside it and is global.

| Scope | Files | Loads |
| --- | --- | --- |
| **Global** | `~/.claude/CLAUDE.md`, `~/.claude/notes/*.md`, the Topical Notes Index | every session, every repo |
| **Project** | `./CLAUDE.md`, `./.claude/docs/*.md`, `~/.claude/projects/<encoded-cwd>/memory/` | only sessions in that one repo |

There is deliberately **no project-scoped notes tier**. Project long-form goes to
`./.claude/docs/<topic>.md`. A fifth tier would mean a second index format and a second
orphan surface for no gain.

## Resolving the project scope

Claude Code names a project directory after the absolute cwd with `/` and `.` each
replaced by `-`. Every other character, including `_` and letter case, is preserved.

This one line is the canonical encoding expression:

<!-- canonical-encoding -->
```sh
enc=$(printf '%s' "$PWD" | sed 's#[/.]#-#g')
```

**Inline it at every point of use - never call it as a helper defined elsewhere.** The Bash
tool persists the working directory between calls but **not** shell functions or variables,
so a function defined in one invocation is unset in the next, `$enc` expands to empty, and
the path collapses to `$HOME/.claude/projects//memory`. That failure surfaces as "this
project has no memory dir yet", which is indistinguishable from the dotted-path bug below.
Re-derive the line as the **first line of the same Bash invocation** that consumes it:

```sh
enc=$(printf '%s' "$PWD" | sed 's#[/.]#-#g')
mem="$HOME/.claude/projects/$enc/memory"
ls -d "$mem" 2>/dev/null || echo "no memory dir for this project yet"
```

**Never resolve with a `*` glob.** `ls -d ~/.claude/projects/*/memory` matches every
project on the machine - 115 of them on a mature setup - so it cannot identify the
current one, and acting on its output edits some other repo's memory.

**Omitting the `.` replacement is the classic bug.** `sed 's#/#-#g'` maps
`/Users/x/.claude` to `-Users-x-.claude`, which does not exist, so the lookup silently
reports "no memory dir" for any path containing a dot - a `.claude` directory, a
`my.app` repo, a worktree under `.claude/worktrees/`. The same encoding locates the
session transcript, so the bug loses that too.

**When the directory does not exist**, the project has no memory yet. Ask before creating
one - do not create it as a side effect of a capture.

**When the session has additional working directories**, resolve against the primary cwd,
and say which project you resolved in the report. Silently picking a different one is the
failure this rule exists to prevent.

## Scope is decided before tier

Ask this **before** the routing tree in `routing-rubric.md`:

> Does this stop being true when I switch to another repo?

- **Yes -> project scope.** Then choose among project homes only: `./CLAUDE.md` for a
  team convention, `./.claude/docs/<topic>.md` for long-form, project memory for a fact
  about the work.
- **No -> global scope.** Only now ask the tool-vs-everywhere question that picks between
  `~/.claude/CLAUDE.md` and `~/.claude/notes/<topic>.md`.

Asking the tier question first is what produces the leak, because a learning can be
tool-shaped **and** repo-bound at the same time. "Our uploads bucket is named lc-prod-uploads
and lives in the us-west Railway project" is repo-specific, so it belongs in project
memory. But if you ask tier first ("is this tool-shaped?"), the tree sends it to the
global `notes/railway.md` - where every other repo's session now loads one repo's
deployment detail. Scope first routes it to project memory, where it stops being true the
moment you `cd` elsewhere.

The mirror case is real too: a fact discovered *while* working in one repo is not thereby
project-scoped. "`gh pr merge` needs the repo-qualified permission rule" was learned
somewhere, but it holds everywhere - global scope.

## The never-cross list

1. **A global note never takes a repo as its subject.** `~/.claude/notes/<topic>.md` is
   about a tool, platform, API, SDK, or service. If its content only makes sense inside
   one repo, it is misfiled - see `audit-checklist.md` check 9.
2. **Project-scoped content never relocates into `~/.claude/notes/`.** Project-scoped means
   the fact stops being true in another repo. When a project file needs to shed weight, that
   detail goes to `./.claude/docs/`, the repo's real docs, or project memory. Relocating it
   globally would leak one repo into every session. This is a rule about the fact's scope,
   not about the file it currently sits in - **the one exception is a fact that is already
   mis-scoped**: a project memory file holding a learning that stays true in any repo is
   global content that merely lives in a project home, and moving it to
   `~/.claude/notes/` (or inline, if it fires every session) is the fix, not a violation -
   see `audit-checklist.md` check 9, second bullet. Test the fact, not the path.
3. **Deltas never pool across scopes.** A global-file delta and a project-file delta are
   different currencies; only global ones feed the no-growth gate. See
   `size-budget.md` and `output-format.md`.
4. **A project-scope backup never lands in the repo working tree.** It goes under
   `~/.claude/notation-backups/<encoded-cwd>/`. See `verify-after-apply.md`.
