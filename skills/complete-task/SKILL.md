---
description: Complete a Jira task — run quality gates, add summary comment, transition to "Done"
user_invocable: true
---

# /complete-task

Finish work on a Jira ticket. Verifies acceptance criteria, runs quality checks, posts a summary and post-mortem, and transitions the issue to "Done".

## Usage

```
/complete-task <ISSUE-KEY>
```

Example: `/complete-task PROJ-123`

## Steps

### Step 1: Fetch the ticket

Use `getJiraIssue` to retrieve current state and confirm it's "In Progress".

### Step 2: Run quality gates

Before completing, verify:
- All tests pass (run the project's test suite)
- No obvious security issues in changed files (grep for hardcoded secrets)
- Changed files are committed
- Test coverage on changed files has not decreased

**Hard gate:** Do not proceed if tests fail or security issues are found.

### Step 3: Verify acceptance criteria

Extract the `Acceptance Criteria` checklist from the ticket description. For each criterion:
- Run the specified verification (test command, file check, behavior walkthrough)
- Record pass/fail with evidence

Generate and post a verification report to Jira:

```markdown
## Acceptance Criteria Verification: <KEY>

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | <criterion> | PASS/FAIL | <how verified> |

**Result:** ALL PASS / <N> FAILURES
```

**Hard gate:** Do not proceed if any criterion fails. List what needs fixing.

### Step 4: Generate summary

Collect:
- Files changed (`git diff --name-only` against the branch start)
- Key decisions made during implementation
- Any deviations from the original ticket description
- Anything the next person should know

### Step 5: Add summary comment

Use `addCommentToJiraIssue` to post the summary in Markdown format.

### Step 6: Generate and post post-mortem

Generate a structured post-mortem following the `/post-mortem` workflow:

```markdown
## Post-Mortem: <KEY> — <Summary>

**Completed:** <date>
**Duration:** <time from In Progress to Done>

### What Went Well
- <positive outcomes>

### What Didn't Go Well
- <issues, unexpected problems, time sinks>

### Lessons Learned
- <actionable insights>

### Metrics
- Files changed: <count>
- Commits: <count>
- Tests added/modified: <count>
- Acceptance criteria met: <X/Y>

### Follow-Up Items
- [ ] <remaining work>
```

Post to Jira using `addCommentToJiraIssue`.

### Step 7: Populate lifecycle fields

Use `editJiraIssue` to write post-mortem data to custom fields (same as `/post-mortem` Step 4):

```
editJiraIssue(issueIdOrKey, fields={
    "customfield_10180": "<What Went Well>",
    "customfield_10181": "<What Didn't Go Well>",
    "customfield_10182": "<Lessons Learned>",
    "customfield_10183": "<Metrics>",
    "customfield_10184": "<Follow-Up Items>",
    "customfield_10192": [
        {"id": "10138"}, {"id": "10139"}, {"id": "10140"},
        {"id": "10141"}, {"id": "10142"}
    ]
})
```

### Step 8: Transition status

Use `getTransitionsForJiraIssue` to discover available transitions at runtime.

**Preferred target:** "Work Complete" (if available in transitions).
**Fallback:** "Done" (transition ID `41`).

This ensures the skill works both before and after the new statuses are added to the board.

```
transitions = getTransitionsForJiraIssue(issueIdOrKey)
target = find transition with to.name == "Work Complete"
if not found: target = find transition with to.name == "Done"
transitionJiraIssue(issueIdOrKey, transition={id: target.id})
```

### Step 9: Check parent epic

If this ticket has a parent epic, use `searchJiraIssuesUsingJql` with `parent = <epic-key> AND status != Done` to check if all sibling tasks are done. If so, note that the epic may be ready to close.

### Step 10: Persist lessons to memory

If the post-mortem contains significant lessons learned:
- Save to a memory file in the project memory directory
- Include enough context for future sessions to apply the lesson

### Step 11: Create follow-up tickets

If follow-up items were identified in the post-mortem:
- Present them to the user
- Offer to create each as a new ticket using `/create-ticket` logic

### Step 12: Output

Confirm completion with a brief summary.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `getTransitionsForJiraIssue` (cloudId, issueIdOrKey) — discover transition IDs at runtime
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id })
- `editJiraIssue` (cloudId, issueIdOrKey, fields) — write lifecycle custom fields
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `searchJiraIssuesUsingJql` (cloudId, jql)
- `createJiraIssue` (cloudId, fields) — for follow-ups
- `createIssueLink` (cloudId, linkType, inwardIssue, outwardIssue) — for follow-ups

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
