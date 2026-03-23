---
description: Jira-first work tracking — automatically search for and create tickets, post updates, include identifiers in commits
globs:
  - "**/*"
---

# Work Tracking — Jira-First Behavior

> Invoke `/workflow` for full gated lifecycle with deterministic enforcement. This rule covers ticket search/create mechanics and is active in all sessions.

All implementation work is tracked in Jira by default. Follow these behaviors automatically without waiting for the user to invoke a skill.

## On any implementation request

Before writing code:

1. **Search Jira** for a matching ticket using `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql`. Search by keywords from the request.
2. **If found:** Set it as the active ticket for the session. Transition to "In Progress" (transition ID `21`) using `mcp__claude_ai_Atlassian__transitionJiraIssue` if not already.
3. **If not found:** Prompt the user: "No Jira ticket found for this work. Should I create one?" If yes, follow the `/create-ticket` workflow to create a structured ticket with acceptance criteria.
4. **Evaluate decomposition:** Before beginning work, assess whether it should be multiple tickets:
   - Multiple independent codebase areas?
   - Independently verifiable acceptance criteria?
   - More than one session of effort?
   - Mix of setup/infrastructure and feature work?

   If decomposition is warranted, present the proposed breakdown to the user. Use `/create-ticket` for each piece, then create "Blocks" links between them using `mcp__claude_ai_Atlassian__createIssueLink`.

## Taxonomy label requirement

When creating or updating tickets, apply taxonomy labels per `.claude/rules/label-taxonomy.md`:

- **Work pattern:** exactly one of `scraper`, `agent`, `workflow`, `deployment`, `pipeline`, `migration`, `platform`
- **Infrastructure layer:** exactly one of `L1-platform`, `L2-services`, `L3-framework`, `L4-domain`
- If work matches a known pattern, offer the standard decomposition template from the label-taxonomy rule
- Cross-project Blocks links must flow downward: L1 → L2 → L3 → L4

## Stale in-progress tickets

At session start, if a ticket is already "In Progress":

1. Check `git log --oneline -20` for recent commits referencing the ticket identifier
2. **If commits exist within ~24h:** Treat it as actively in progress — resume normally
3. **If the last relevant commit is older than 24h:** Note the gap to the user and ask whether to resume or restart
4. **If no commits reference the identifier at all:** Flag it as potentially stale — ask the user to confirm intent before proceeding

Do not silently assume a stale In Progress ticket is active work.

## Exceptions

- **Trivial changes** (typo fixes, single-line formatting, comment updates) skip tracking
- The user can say **"skip tracking"** to bypass for any change
- If the user explicitly says they don't want a ticket, respect that and don't ask again in the session

## Suggesting next work

When a ticket is completed or the user asks what to work on next:

1. Use `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql` with `project = LAB AND statusCategory in ("To Do") ORDER BY priority DESC`
2. For each candidate, use `mcp__claude_ai_Atlassian__getJiraIssue` and check `issuelinks` for "is blocked by" links
3. A ticket is **eligible** only if all blocking tickets are Done (or it has no blockers)
4. Present eligible items ordered by priority, noting any that just became unblocked

If no eligible items exist, report which blockers need resolving to unlock the next tier of work.
