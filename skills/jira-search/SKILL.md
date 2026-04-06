---
description: "Search Jira issues using JQL and display results as a formatted table"
user_invocable: true
---

# /jira-search

Search Jira issues using JQL and display results in a readable table format.

## Usage

```
/jira-search
/jira-search <JQL query>
```

Example: `/jira-search project = LAB AND status = "In Progress"`

## Steps

1. **Write skill execution context marker:** Write `.skill-execution-context.json` with: `{"skill": "jira-search", "started_at": "<ISO8601>", "ticket_key": null}`

2. **Parse the JQL query** from the user's input after `/jira-search`. If no query provided, use `project = LAB ORDER BY updated DESC` as default.

3. **Execute search** using `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql`:
   - cloudId: `fredabood.atlassian.net`
   - jql: the parsed query
   - maxResults: 20
   - fields: `["summary", "status", "priority", "labels", "assignee", "updated"]`

4. **Format results** as a markdown table:

   ```
   ## Jira Search Results

   **Query:** `<JQL>`
   **Results:** X issues found

   | Key | Summary | Status | Priority | Labels | Updated |
   |-----|---------|--------|----------|--------|---------|
   | LAB-123 | Example issue | In Progress | Medium | platform, L3-framework | 2026-04-05 |
   ```

   - Show total count from the response
   - If no results, display: "No issues found for this query."
   - Truncate summary to 60 characters if longer, with ellipsis
   - Format updated date as YYYY-MM-DD (date only, no time)
   - Show assignee display name if set, or "-" if unassigned

5. **Cleanup:** Delete `.skill-execution-context.json`.

## Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql, maxResults, fields)

## CloudId

Use `fredabood.atlassian.net` as the cloudId for all queries.
