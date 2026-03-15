---
description: Complete a Jira task — run quality gates, add summary comment, transition to "Done"
user_invocable: true
---

# /complete-task

Finish work on a Jira ticket. Runs quality checks, adds a summary comment documenting what was done, and transitions the issue to "Done".

## Usage

```
/complete-task <ISSUE-KEY>
```

Example: `/complete-task VIBEY-123`

## Steps

1. **Fetch the ticket** — Use `getJiraIssue` to retrieve current state and confirm it's "In Progress"

2. **Run quality gates** — Before completing, verify:
   - All tests pass (run the project's test suite)
   - No obvious security issues in changed files (grep for hardcoded secrets)
   - Changed files are committed

3. **Generate summary** — Collect:
   - Files changed (`git diff --name-only` against the branch start)
   - Key decisions made during implementation
   - Any deviations from the original ticket description
   - Anything the next person should know

4. **Add summary comment** — Use `addCommentToJiraIssue` to post the summary in Markdown format

5. **Transition to Done** — Call `transitionJiraIssue` with transition ID `"31"` to move the ticket to "Done"

6. **Check parent epic** — If this ticket has a parent epic, use `searchJiraIssuesUsingJql` with `parent = <epic-key> AND status != Done` to check if all sibling tasks are done. If so, note that the epic may be ready to close.

7. **Output** — Confirm completion with a brief summary.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id: "31" })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `searchJiraIssuesUsingJql` (cloudId, jql)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
