---
description: Capture this session's learnings and route each one to the right memory tier - global CLAUDE.md, ~/.claude/notes/, per-project MEMORY.md, or project docs. Keeps CLAUDE.md lean.
allowed-tools: ["Read", "Edit", "Write", "Glob", "Bash"]
disable-model-invocation: true
---

# /notation:notate

Turn what you learned this session into durable, well-placed notation. The job is not "append to CLAUDE.md" - it is to send each learning to the **one tier where it belongs**, defaulting away from CLAUDE.md so it stays small and fast.

Read the full decision tree at `${CLAUDE_PLUGIN_ROOT}/skills/notation-audit/references/routing-rubric.md` if a learning is hard to place. The compact version is below.

## Step 1 - Reflect

List the candidate learnings from this session. Look for:
- Commands, flags, or invocations that were discovered or corrected
- Gotchas, error messages, and their resolutions
- Config / environment quirks
- Code-style or testing patterns that worked
- Project-specific architecture or decisions not derivable from the code itself
- Corrections the user made to how you worked

Drop anything that is a one-off unlikely to recur, or already obvious from the code/README/git history. Quality over volume.

## Step 2 - Route each learning (do NOT dump)

Classify every surviving learning into exactly one tier:

| Signal | Tier | Destination |
| --- | --- | --- |
| High-frequency, cross-project, fires almost every session (permission/CLI/session quirks) | **Global rules** | `~/.claude/CLAUDE.md` (inline) |
| Situational, tied to one tool / platform / API / SDK / service; useful only when that thing comes up | **Topical note** | `~/.claude/notes/<topic>.md` + a line in the Topical Notes Index |
| Specific to THIS project's architecture, decisions, gotchas, or workflow; not in the code | **Project memory** | this project's `MEMORY.md` + a frontmatter memory file |
| A team-shared convention others on the repo need | **Project CLAUDE.md** | `./CLAUDE.md` (only if the repo tracks one) |
| A large guide / spec / phase write-up | **Project docs** | `./.claude/docs/<name>.md` |

**Lean bias (the whole point):** if a learning is tool- or platform-specific, it goes to `notes/`, NOT inline into CLAUDE.md - even if it feels important. Only promote to global CLAUDE.md when it genuinely applies regardless of what you are working on. When in doubt, prefer `notes/` or project memory over CLAUDE.md.

Announce the routing as a short list before touching any file, e.g.:
- "gh repo create classifier block" -> global CLAUDE.md (fires across repos)
- "Railway bucket TTL trick" -> notes/railway.md (one platform)
- "this service gates AI providers behind env X" -> project memory

## Step 3 - Dedup against the destination (targeted reads only)

For each routed learning, read ONLY the destination file (and the relevant section), not the whole tree. Do not run a repo-wide `find`. Locations are known:
- Global rules + index: `~/.claude/CLAUDE.md`
- Notes: `~/.claude/notes/` (`Glob` it)
- Project memory: the per-project memory dir (see Step 5)
- Project CLAUDE.md / docs: `./CLAUDE.md`, `./.claude/docs/`

If the learning is already covered, **update in place** rather than adding a duplicate. If a `notes/` file for the topic already exists, append to it; only create a new note when no topic file fits.

## Step 4 - Back up before editing global CLAUDE.md

If (and only if) you will edit `~/.claude/CLAUDE.md`, snapshot it first:
```bash
cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak.$(date +%Y%m%d-%H%M%S)
```
No backup needed for notes, memory, or project files.

## Step 5 - Tier-specific formatting

**Topical note (`~/.claude/notes/<topic>.md`):**
- Markdown with `##` section headings and fenced code blocks for commands.
- After writing/creating the note, ensure the **Topical Notes Index** at the bottom of `~/.claude/CLAUDE.md` has a one-line entry: `` - [`notes/<topic>.md`](notes/<topic>.md) - <hook> ``. Add it if missing; leave it alone if already present. (Creating/updating a note is a notes edit - the index line is the only CLAUDE.md change, and it does not require the Step 4 backup unless you are also editing rules inline.)

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
- Add a one-line pointer to that dir's `MEMORY.md`: `- [Title](file.md) - hook`. Never put the fact body in `MEMORY.md`; it is the index only.
- Before creating, check for an existing memory file covering the same fact and update it instead.

**Global CLAUDE.md rule:** one line per concept, in the most relevant existing section. Format `` `<command/pattern>` - <brief note> ``. No verbose prose.

**Project CLAUDE.md / docs:** match the file's existing style.

## Step 6 - Show grouped proposals, apply on approval

Present proposed changes **grouped by destination tier**, each with a one-line "Why" and a short diff. Then ask the user which to apply. Edit only approved items, and keep each content change atomic with its index update (note + Topical Notes Index line together; memory file + MEMORY.md pointer together).

Never edit `~/.claude/settings.json` (the harness self-grant guard blocks it, and it is not a notation target).

## Output style
- Use plain hyphens (`-`) only. No em-dashes or en-dashes anywhere you write.
- Be concise. Reference files by absolute path.
