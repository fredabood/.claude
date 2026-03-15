---
description: Start working on a Jira task — transitions it to "In Progress" and sets context
user_invocable: true
---

# /start-task

Start working on a Jira ticket. Checks acceptance criteria, transitions the issue to "In Progress", adds a context comment, and sets up the working context for the session.

## Usage

```
/start-task <ISSUE-KEY>
```

Example: `/start-task PROJ-123`

## Steps

### Step 1: Fetch the ticket

Use `getJiraIssue` to retrieve the issue details (summary, description, acceptance criteria, status, assignee).

### Step 2: Validate state

Confirm the ticket is not already "Done". If it's already "In Progress", note that and skip the transition.

### Step 3: Check for blockers

Inspect the ticket's issue links (from the `getJiraIssue` response in Step 1):

1. Examine `issuelinks` for inward links where `type.name == "Blocks"` ("is blocked by")
2. For each blocking issue, check its status

**If all blockers are Done (or no blockers):** Proceed.

**If any blocker is not Done:** Display:
```
Warning: This ticket has unresolved blockers:
- BLOCKER-KEY: <summary> (status: <status>)
```

Ask the user whether to:
- Proceed anyway (acknowledge risk of rework)
- Switch to a blocker instead (suggest highest-priority unresolved blocker)
- View next-eligible tickets (no unresolved blockers)

### Step 4: Check acceptance criteria

Parse the ticket description for an `Acceptance Criteria` section.

- **If criteria exist:** Confirm they are measurable and deterministic. Display them for the session.
- **If criteria are missing:** Prompt: "This ticket has no acceptance criteria. Would you like me to draft some before we begin?"
  - If the user agrees, draft criteria based on the description following the standard format:
    ```
    ## Acceptance Criteria
    - [ ] <Specific verifiable condition>
    - [ ] Tests pass: `<command>`
    - [ ] No security regressions
    - [ ] Documentation updated (if applicable)
    ```
  - Post the drafted criteria as a Jira comment using `addCommentToJiraIssue` (or suggest editing the description).
  - If the user declines, note the gap and proceed.

### Step 5: Transition to In Progress

Call `transitionJiraIssue` with transition ID `"21"` to move the ticket to "In Progress".

### Step 6: Add a context comment

Use `addCommentToJiraIssue` to post:
```
Starting work on this ticket.
Session: [current date/time]
```

### Step 7: Set working context

Summarize the ticket for the session:
- Issue key and summary
- Description / acceptance criteria
- Tickets this blocks (outward links) — work waiting on this ticket
- Tickets this is blocked by (inward links) — with current status
- Relevant files (if mentioned in the ticket)

### Step 8: Output

Display a brief summary confirming the task is started and what needs to be done.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id: "21" })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
