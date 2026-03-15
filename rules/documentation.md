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
| Ticket-specific (approach choice, trade-off for this task) | Jira comment on the ticket |
| Project-scoped (convention, pattern, architectural decision) | Memory file in the project memory directory |
| Operational (how to run, deploy, configure, troubleshoot) | `docs/` directory |

## On session end or handoff

Ensure decisions and learnings from the session are persisted — not just outputted to the conversation. Use the `/handoff` workflow to persist to Jira + memory.

## Documentation locations

- **`docs/`** — Operational docs: how-tos, architecture overviews, runbooks. Canonical reference for how the system works.
- **Memory files** — Long-term knowledge, cross-session decisions, lessons learned. Inform future Claude sessions.
- **Jira comments** — Ticket-specific context: plans, milestones, post-mortems, verification reports. Audit trail for individual work items.
- **CLAUDE.md** — Project-level workflow conventions and Jira configuration. Rarely changes; only updated when conventions evolve.

## What not to document

- Don't add comments to self-explanatory code
- Don't create docs for one-off scripts or throwaway work
- Don't duplicate information that's already in the code, git history, or Jira
