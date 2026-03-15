---
description: Start working on a Jira task — transitions it to "In Progress" and sets context
user_invocable: true
---

# /start-task

Start working on a Jira ticket. Transitions the issue to "In Progress", adds a context comment, and sets up the working context for the session.

## Usage

```
/start-task <ISSUE-KEY>
```

Example: `/start-task VIBEY-123`

## Steps

1. **Fetch the ticket** — Use `getJiraIssue` to retrieve the issue details (summary, description, acceptance criteria, status, assignee)

2. **Validate state** — Confirm the ticket is not already "Done". If it's already "In Progress", note that and skip the transition.

3. **Transition to In Progress** — Call `transitionJiraIssue` with transition ID `"21"` to move the ticket to "In Progress"

4. **Add a context comment** — Use `addCommentToJiraIssue` to post:
   ```
   Starting work on this ticket.
   Session: [current date/time]
   ```

5. **Set working context** — Summarize the ticket for the session:
   - Issue key and summary
   - Description / acceptance criteria
   - Any linked issues or blockers
   - Relevant files (if mentioned in the ticket)

6. **Output** — Display a brief summary confirming the task is started and what needs to be done.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id: "21" })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
