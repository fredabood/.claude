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
5. **If Assigned Agent is set** and differs from the current session: another agent started but did not finish — warn the user and ask whether to take over or leave it

Do not silently assume a stale In Progress ticket is active work.

## Exceptions

- **Trivial changes** (typo fixes, single-line formatting, comment updates) skip tracking
- The user can say **"skip tracking"** to bypass for any change
- If the user explicitly says they don't want a ticket, respect that and don't ask again in the session

## Agent assignment protocol

Before transitioning a ticket to "In Progress":

1. Set `Assigned Agent` to the current session identifier (requires custom field from LAB-628; until then, post assignment as a Jira comment)
2. Transition to "In Progress" using `getTransitionsForJiraIssue` to discover the transition ID
3. Post context comment: "Starting work. Assigned Agent: `<session-id>`. Session: `<timestamp>`"

If the ticket already has an `Assigned Agent` set:
- **Same agent:** Resume normally
- **Different agent:** Warn the user that another agent claimed this ticket — ask whether to override or pick a different ticket

## Suggesting next work (Planned+Unblocked agent queue)

When a ticket is completed or the user asks what to work on next, use the agent work queue
defined in `.claude/rules/label-taxonomy.md`:

1. **Query base candidates:**
   ```
   project = LAB AND status = "To Do" AND description ~ "Acceptance Criteria"
     ORDER BY priority DESC, created ASC
   ```
2. For each candidate, use `mcp__claude_ai_Atlassian__getJiraIssue` and apply three filters:
   - **Planned check:** Verify a plan comment exists (comment body contains structured plan sections)
   - **Blocker check:** Inspect `issuelinks` for inward "Blocks" links — all blockers must be in status category "Done"
   - **Assignment check:** If Assigned Agent is set and ≠ current agent, skip
3. A ticket is **eligible** only if: Planned = true AND Blocked = false AND (unassigned or assigned to current agent)
4. Present results in three tiers:
   - **Ready for pickup:** Eligible items, ordered by priority
   - **Blocked:** Planned but waiting on dependencies — show which blockers are closest to completion
   - **Needs planning:** Missing acceptance criteria or plan comment — note what's missing
5. For blocked candidates, identify which blockers are closest to completion

If no eligible items exist, report: (a) unplanned tickets that need criteria/plans, (b) which blockers need resolving to unlock the next tier.
