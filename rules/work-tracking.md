---
description: Jira-first work tracking — automatically search for and create tickets, post updates, include ticket keys in commits
globs:
  - "**/*"
---

# Work Tracking — Jira-First Behavior

All implementation work is tracked in Jira by default. Follow these behaviors automatically without waiting for the user to invoke a skill.

## On any implementation request

Before writing code:

1. **Search Jira** for a matching ticket using `searchJiraIssuesUsingJql`. Search by keywords from the request.
2. **If found:** Set it as the active ticket for the session. Transition to "In Progress" (transition ID `"21"`) if not already.
3. **If not found:** Prompt the user: "No Jira ticket found for this work. Should I create one?" If yes, follow the `/create-ticket` workflow to create a structured ticket with acceptance criteria.
4. **Evaluate decomposition:** Before beginning work, assess whether it should be multiple tickets:
   - Multiple independent codebase areas?
   - Independently verifiable acceptance criteria?
   - More than one session of effort?
   - Mix of setup/infrastructure and feature work?

   If decomposition is warranted, present the proposed breakdown to the user. Use `/create-ticket` for each piece, then create "Blocks" links between them.

## During implementation

Post Jira comments automatically when:
- A **design decision** is made (especially deviations from the ticket description)
- The **approach changes** from what was originally planned
- A **blocker** is encountered
- A **significant milestone** is reached (e.g., tests passing, migration applied, integration working)

Use `addCommentToJiraIssue` with a concise Markdown summary.

## On commit

Ensure every commit message includes the active ticket key in the format `KEY-123: <description>`.

## Stale in-progress tickets

At session start, if a ticket is already "In Progress":

1. Check `git log --oneline -20` for recent commits referencing the ticket key
2. **If commits exist within ~24h:** Treat it as actively in progress — resume normally
3. **If the last relevant commit is older than 24h:** Note the gap to the user and ask whether to resume or restart the ticket
4. **If no commits reference the ticket at all:** Flag it as potentially stale — ask the user to confirm intent before proceeding

Do not silently assume a stale In Progress ticket is active work.

## Exceptions

- **Trivial changes** (typo fixes, single-line formatting, comment updates) skip tracking
- The user can say **"skip tracking"** to bypass for any change
- If the user explicitly says they don't want a ticket, respect that and don't ask again in the session

## Suggesting next work

When a ticket is completed or the user asks what to work on next:

1. Query: `project = <KEY> AND status = "To Do" AND sprint in openSprints() ORDER BY priority DESC`
2. For each candidate, call `getJiraIssue` to retrieve issue links
3. Check inward "is blocked by" links — a ticket is **eligible** only if all blocking issues are Done (or it has no blockers)
4. Present eligible tickets ordered by priority, noting any that just became unblocked

If no eligible tickets exist, report which blockers need resolving to unlock the next tier of work.
