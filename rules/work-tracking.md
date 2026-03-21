---
description: Plane-first work tracking — automatically search for and create work items, post updates, include identifiers in commits
globs:
  - "**/*"
---

# Work Tracking — Plane-First Behavior

All implementation work is tracked in Plane by default. Follow these behaviors automatically without waiting for the user to invoke a skill.

## On any implementation request

Before writing code:

1. **Search Plane** for a matching work item using `mcp__plane__search_work_items`. Search by keywords from the request.
2. **If found:** Set it as the active work item for the session. Transition to "In Progress" (state `38a9fff5-0713-471c-8b8c-4523406e1416`) using `mcp__plane__update_work_item` if not already.
3. **If not found:** Prompt the user: "No Plane work item found for this work. Should I create one?" If yes, follow the `/create-ticket` workflow to create a structured work item with acceptance criteria.
4. **Evaluate decomposition:** Before beginning work, assess whether it should be multiple work items:
   - Multiple independent codebase areas?
   - Independently verifiable acceptance criteria?
   - More than one session of effort?
   - Mix of setup/infrastructure and feature work?

   If decomposition is warranted, present the proposed breakdown to the user. Use `/create-ticket` for each piece, then create "blocks" relations between them using `mcp__plane__create_work_item_relation`.

## During implementation

Post Plane comments automatically when:
- A **design decision** is made (especially deviations from the work item description)
- The **approach changes** from what was originally planned
- A **blocker** is encountered
- A **significant milestone** is reached (e.g., tests passing, migration applied, integration working)

Use `mcp__plane__create_work_item_comment` with a concise Markdown summary.

## On commit

Ensure every commit message includes the active work item identifier in the format `KEY-123: <description>`.

## Stale in-progress work items

At session start, if a work item is already "In Progress":

1. Check `git log --oneline -20` for recent commits referencing the work item identifier
2. **If commits exist within ~24h:** Treat it as actively in progress — resume normally
3. **If the last relevant commit is older than 24h:** Note the gap to the user and ask whether to resume or restart
4. **If no commits reference the identifier at all:** Flag it as potentially stale — ask the user to confirm intent before proceeding

Do not silently assume a stale In Progress item is active work.

## Exceptions

- **Trivial changes** (typo fixes, single-line formatting, comment updates) skip tracking
- The user can say **"skip tracking"** to bypass for any change
- If the user explicitly says they don't want a ticket, respect that and don't ask again in the session

## Suggesting next work

When a work item is completed or the user asks what to work on next:

1. Use `mcp__plane__list_work_items` for the `LAB` project filtered to open states (Todo/Backlog)
2. For each candidate, call `mcp__plane__list_work_item_relations` to check "blocked_by" relations
3. A work item is **eligible** only if all blocking items are Done (or it has no blockers)
4. Present eligible items ordered by priority, noting any that just became unblocked

If no eligible items exist, report which blockers need resolving to unlock the next tier of work.
