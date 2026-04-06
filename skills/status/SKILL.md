---
description: Show project status from Jira — active sprint, ticket states, blockers
user_invocable: true
---

# /status

**Before any Jira operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "status", "started_at": "<current ISO8601 timestamp>", "ticket_key": null}`

Query Jira for a project overview showing active work, blockers, and progress.

## Usage

```
/status
/status <PROJECT-KEY>
```

Example: `/status` or `/status VIBEY`

## Steps

1. **Determine project** — Use the project key from the argument, or infer from CLAUDE.md / recent git history

2. **Query active sprint** — Use `searchJiraIssuesUsingJql`:
   ```
   project = <KEY> AND sprint in openSprints() ORDER BY status ASC, priority DESC
   ```

3. **Query blockers** — Use `searchJiraIssuesUsingJql`:
   ```
   project = <KEY> AND status != Done AND (labels = blocker OR priority = Highest)
   ```

4. **Compute next-eligible tickets:**
   a. Query: `project = <KEY> AND status = "To Do" AND sprint in openSprints() ORDER BY priority DESC`
   b. For each candidate, `getJiraIssue(cloudId, issueKey)` to retrieve links
   c. Check inward "is blocked by" links:
      - No such links → eligible
      - All blocking issues Done → eligible (note: "just unblocked")
      - Otherwise → blocked (record which blockers are unresolved)
   d. Collect eligible set ordered by priority

5. **Format overview** — Display a structured summary:

   ```
   ## Project Status: <PROJECT-KEY>

   ### Active Sprint: <sprint name>
   | Key | Summary | Status | Assignee |
   |-----|---------|--------|----------|
   | ... | ...     | ...    | ...      |

   ### Progress
   - To Do: X
   - In Progress: Y
   - Done: Z

   ### Blockers
   - <KEY>: <summary> (reason)

   ### Next Eligible (ready to start)
   | Key | Summary | Priority | Notes |
   |-----|---------|----------|-------|
   | ... | ...     | High     | No blockers / Just unblocked |

   ### Blocked (waiting on dependencies)
   | Key | Summary | Blocked By | Blocker Status |
   |-----|---------|-----------|----------------|
   | ... | ...     | KEY-X     | In Progress    |
   ```

6. **Output** — Display the formatted overview.

## Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)
- `getJiraIssue` (cloudId, issueIdOrKey)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
