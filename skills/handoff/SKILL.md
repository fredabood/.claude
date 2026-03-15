---
description: Generate a session handoff summary for continuity between conversations
user_invocable: true
---

# /handoff

Generate a session handoff summary and persist it to Jira and memory for continuity across conversations.

## Usage

```
/handoff
```

## Steps

### Step 1: Collect session activity

- Files changed: `git diff --name-only` (staged and unstaged)
- Commits made: `git log --oneline` since session start (compare to recent history)
- Jira tickets touched (any tickets transitioned, commented on, or created during the session)

### Step 2: Summarize work done

- What features were implemented or bugs fixed
- What tests were added or updated
- What documentation was changed

### Step 3: Capture decisions

- Any design choices made and their rationale
- Any trade-offs accepted
- Any deviations from the original plan

### Step 4: Identify open items

- Uncommitted changes and their purpose
- Failing tests or known issues
- Tickets still in progress
- Next steps that should be taken

### Step 5: Note blockers

- Anything that prevented completion
- Questions that need answers
- External dependencies waiting on

### Step 6: Format handoff

```markdown
## Session Handoff — <date>

### Completed
- <what was done>

### Decisions
- <decision and why>

### Open Items
- <what's pending>

### Blockers
- <what's blocked and why>

### Next Steps
1. <recommended next action>
2. <follow-up>

### Files Changed
- <file list>
```

### Step 7: Post to Jira

For each ticket touched during the session, use `addCommentToJiraIssue` to post the relevant subset of the handoff summary as a comment. Each ticket gets only the context relevant to it — not the full handoff.

### Step 8: Save to memory

Write or update memory files in the project memory directory with:
- Session context and decisions that the next conversation needs
- Open items and their current state
- Lessons learned during the session (if significant)

### Step 9: Update docs if needed

If project-level documentation or conventions changed during the session, ensure `docs/` is updated and changes are committed.

## Required MCP Tools

- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
