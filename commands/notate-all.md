---
description: Capture this session's learnings, route each to the right memory tier, and apply every proposal automatically - no interactive picker. Same routing and lean-CLAUDE.md bias as /notation:notate, just without the strategy question. Still prints proposals and backs up CLAUDE.md.
allowed-tools: ["Read", "Edit", "Write", "Glob", "Bash", "AskUserQuestion"]
disable-model-invocation: true
---

# /notation:notate-all

This is `/notation:notate` in auto-apply mode: capture this session's learnings, route each to the tier where it belongs, and apply **all** proposals without the strategy picker.

Read and follow `${CLAUDE_PLUGIN_ROOT}/commands/notate.md` Steps 1-5 exactly (session + project grounding, extracting proposals, routing, dedup, tier-specific formatting). Then run Step 6 in **auto-apply mode**:

- **Print all proposals as text** first (grouped by tier, high-confidence first, with the one-line why and the short diff) - the same printout Step 6 calls for.
- **Skip every `AskUserQuestion`.** Do not ask the strategy question or per-tier multi-selects. Treat every proposal as approved.
- **Apply all proposals**, keeping each content change atomic with its index update (a note with its Topical Notes Index line; a memory file with its `MEMORY.md` pointer).
- **Back up `~/.claude/CLAUDE.md`** before any inline rule edit, exactly as Step 6 specifies.
- **Summarize** what was applied, grouped by tier, by absolute path - noting it auto-applied all N proposals.
