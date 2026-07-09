Dump current session context to orient a new conversation or prepare for /handoff.

1. Run git log --oneline -10 to show recent commits
2. Run git status --short to show modified/staged files
3. Scan recent commit messages for an issue key (pattern: (HL|DD|LAB|DRTY|LEGACY)-\d+) and
   resolve the most recent match to a GitHub issue: HL-<n> → fredabood/homelab #n,
   DD-<n> → fredabood/dirtydata #n; migrated keys (LAB/DRTY/LEGACY) via the mirror:
   docker exec postgres-memory psql -U postgres -d agent_memory -tA -c
   "SELECT gh_repo, gh_number FROM jira.issues WHERE issue_key = '<KEY>'"
4. If an issue is found, fetch it with mcp__github__issue_read (method get for state/board
   status context, method get_comments for the latest comment) and show its status and the
   most recent comment's first line + timestamp

Present:
- Active issue: key + title (or "none found in recent commits")
- Recent commits: last 5, one-line format
- Modified files: staged and unstaged
- Issue state/status + last comment (if found)
