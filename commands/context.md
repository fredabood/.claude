Dump current session context to orient a new conversation or prepare for /handoff.

1. Run git log --oneline -10 to show recent commits
2. Run git status --short to show modified/staged files
3. Scan recent commit messages for a Jira ticket key (pattern: LAB-\d+) and call getJiraIssue on the most recent match
4. If a ticket is found, show its status and the most recent Jira comment title + timestamp

Present:
- Active ticket: key + summary (or "none found in recent commits")
- Recent commits: last 5, one-line format
- Modified files: staged and unstaged
- Ticket status + last comment (if found)
