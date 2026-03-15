---
description: Generate a session handoff summary for continuity between conversations
user_invocable: true
---

# /handoff

Generate a summary of the current session for continuity. Captures what was done, what's pending, key decisions, and context the next session needs.

## Usage

```
/handoff
```

## Steps

1. **Collect session activity:**
   - Files changed: `git diff --name-only` (staged and unstaged)
   - Commits made: `git log --oneline` since session start (compare to recent history)
   - Jira tickets touched (if any `/start-task` or `/complete-task` was used)

2. **Summarize work done:**
   - What features were implemented or bugs fixed
   - What tests were added or updated
   - What documentation was changed

3. **Capture decisions:**
   - Any design choices made and their rationale
   - Any trade-offs accepted
   - Any deviations from the original plan

4. **Identify open items:**
   - Uncommitted changes and their purpose
   - Failing tests or known issues
   - Tickets still in progress
   - Next steps that should be taken

5. **Note blockers:**
   - Anything that prevented completion
   - Questions that need answers
   - External dependencies waiting on

6. **Format and output:**

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

## Notes

This skill produces output in the conversation — it does not write to a file or update Jira. Copy the output to wherever makes sense for your workflow (Jira comment, CLAUDE.md memory, etc.).
