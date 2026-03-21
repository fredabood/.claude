Query Jira for the next eligible tickets in the current sprint.

1. Use searchJiraIssuesUsingJql: project = LAB AND sprint in openSprints() AND status = "To Do" ORDER BY priority DESC
2. For each ticket returned (up to 10), call getJiraIssue to retrieve its issue links
3. Filter out any ticket that has an inward "is blocked by" link where the blocking issue status is not Done
4. Present the top 3 eligible tickets as a prioritized list: key, summary, priority, and a 1-sentence description

If no eligible tickets exist, report which blockers need resolving to unlock the next tier of work.
