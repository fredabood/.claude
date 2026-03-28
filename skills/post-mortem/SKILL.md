---
description: Generate a structured post-mortem for a completed ticket — what went well, what didn't, lessons learned, metrics
user_invocable: true
---

# /post-mortem

Generate and post a structured post-mortem for a Jira ticket. Captures outcomes, issues, lessons, and follow-up items.

## Usage

```
/post-mortem <ISSUE-KEY>
```

Example: `/post-mortem PROJ-123`

## Steps

### Step 1: Fetch ticket details

Use `getJiraIssue` to retrieve the full ticket including:
- Summary, description, status
- All comments (timeline of work)
- Created date, resolution date
- Acceptance criteria

### Step 2: Gather context

- Query postgres for linked commits: `SELECT commit_short, repo, message, committed_at FROM jira.commit_links WHERE issue_key = '<KEY>' ORDER BY committed_at` (via `docker exec postgres-memory psql`)
- Fallback: `git log --grep="<KEY>" --oneline` if postgres unavailable
- Run `git log --grep="<KEY>" --stat` for files changed
- Review ticket comments for the timeline of events (milestones, blockers, decisions)

### Step 3: Generate structured post-mortem

```markdown
## Post-Mortem: <KEY> — <Summary>

**Completed:** <date>
**Duration:** <time from In Progress to Done>

### What Went Well
- <positive outcomes, smooth implementations, good decisions>

### What Didn't Go Well
- <issues encountered, unexpected problems, time sinks, blockers>

### Lessons Learned
- <actionable insights that should inform future work>

### Metrics
- Files changed: <count>
- Commits: <count>
- Tests added/modified: <count>
- Acceptance criteria met: <X/Y>

### Follow-Up Items
- [ ] <remaining work, tech debt, improvements identified>
```

Base the content on actual evidence from git history and Jira comments — don't fabricate or guess.

### Step 4: Populate post-mortem fields

Use `editJiraIssue` to write each section to its custom field:

```
editJiraIssue(issueIdOrKey, fields={
    "customfield_10180": "<What Went Well text>",
    "customfield_10181": "<What Didn't Go Well text>",
    "customfield_10182": "<Lessons Learned text>",
    "customfield_10183": "<Metrics text>",
    "customfield_10184": "<Follow-Up Items text>",
    "customfield_10192": [
        {"id": "10138"},   // What Went Well
        {"id": "10139"},   // What Didn't
        {"id": "10140"},   // Lessons Learned
        {"id": "10141"},   // Metrics
        {"id": "10142"}    // Follow-Ups
    ]
})
```

Field IDs reference `.claude/rules/custom-fields.md`.

### Step 5: Post to Jira

Use `addCommentToJiraIssue` to post the full post-mortem on the ticket (in addition to the field writes — the comment serves as a human-readable record).

### Step 5: Persist to memory

If the post-mortem contains significant lessons learned (patterns to repeat, mistakes to avoid, architectural insights):
- Save to a memory file in the project memory directory
- Include enough context that a future session can apply the lesson without the original ticket context

### Step 6: Create follow-up tickets

If follow-up items were identified:
1. Present them to the user
2. Offer to create each as a new ticket using `/create-ticket` logic
3. Link follow-up tickets to the original ticket

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `createJiraIssue` (cloudId, fields) — for follow-ups
- `createIssueLink` (cloudId, linkType, inwardIssue, outwardIssue) — for follow-ups

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
