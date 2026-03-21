---
description: Documentation as a first-class concern — automatically update docs, persist decisions, and maintain knowledge across sessions
globs:
  - "**/*"
---

# Documentation — First-Class Concern

Documentation is not a final step — it happens throughout the workflow. Follow these behaviors automatically.

## On any code change

Evaluate whether documentation needs updating. If the change affects behavior described in `docs/`, update the docs in the same commit. Don't leave docs out of sync with code.

## On any design decision

Persist the decision and rationale to the appropriate location:

| Decision scope | Where to persist |
|---|---|
| Ticket-specific (approach, trade-off) | Plane comment on the work item |
| Claude behavioral (user prefs, feedback, corrections) | Auto-memory (`~/.claude/projects/.../memory/`) |
| Architectural decision (chose X over Y because Z) | Vault → `submodules/memory/homelab/decisions/` |
| Operational knowledge (how to run, deploy, configure) | Vault → `submodules/memory/homelab/knowledge/` |
| Research findings (evaluation, comparison, analysis) | Vault → `submodules/memory/homelab/research/` |
| Session continuity (handoff context) | Vault → `submodules/memory/homelab/sessions/` |
| Workflow conventions (Plane config, commit format) | CLAUDE.md (rarely) |

## On session end or handoff

Ensure decisions and learnings from the session are persisted — not just outputted to the conversation. Use the `/handoff` workflow to persist to Plane + memory.

## Documentation locations

- **`docs/`** — Operational docs: how-tos, architecture overviews, runbooks. Canonical reference for how the system works.
- **Auto-memory** (`~/.claude/projects/.../memory/`) — Claude behavioral context: user prefs, feedback, references. Auto-loaded, zero friction.
- **Vault** (`submodules/memory/`) — Durable project knowledge: decisions, research, operational knowledge, session handoffs. Git-backed, human-readable.
- **Plane comments** — Work item context: plans, milestones, post-mortems, verification reports. Audit trail for individual work items.
- **CLAUDE.md** — Project-level workflow conventions and Plane configuration. Rarely changes; only updated when conventions evolve.

## Vault: update existing vs. create new

Before writing to the vault, search for an existing note on the same topic:
- Use the obsidian MCP to search by title and aliases
- If a relevant note exists: **update it** — add new information, correct outdated sections
- If no relevant note exists: **create a new one** using `/vault-add`

**Update** an existing note when:
- Adding more detail to the same decision, technology, or entity
- Correcting or superseding previously recorded information
- Appending a new finding to ongoing research

**Create** a new note when:
- The content is a distinct new decision (different trade-off, different date)
- A new research finding stands independently from prior analysis
- A new session handoff with its own context

When in doubt, prefer updating over creating — fragmentation makes future retrieval harder.

## What not to document

- Don't add comments to self-explanatory code
- Don't create docs for one-off scripts or throwaway work
- Don't duplicate information that's already in the code, git history, or Plane
