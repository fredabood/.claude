Surface all open Jira tickets that are currently blocked by an unresolved issue.

1. Use searchJiraIssuesUsingJql: project = LAB AND status in ("To Do", "In Progress")
2. For each returned ticket, call getJiraIssue and inspect issue links for "is blocked by" relationships
3. For each blocking relationship, check if the blocker status is Done — if not, this is an active blocker
4. Present a table: blocked ticket | blocker ticket | blocker status | blocker summary

Only show tickets with active (unresolved) blockers. If none, confirm the board is clear.
