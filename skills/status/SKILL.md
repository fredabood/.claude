---
name: status
description: Show project status from GitHub Issues — board snapshot, blockers, next-eligible work, recent closes
user_invocable: true
---

# /status

**Before any GitHub issue operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "status", "started_at": "<current ISO8601 timestamp>", "ticket_key": null}`

Show a project overview from the "Homelab Work" board and the postgres mirror: open work by Status, blockers, next-eligible issues, and recent completions.

## Usage

```
/status
/status <repo>
```

Example: `/status` (both repos) or `/status homelab` or `/status dirtydata`

## Steps

1. **Determine scope** — Use the repo from the argument (`homelab` or `dirtydata`), or default to both. The mirror (`jira.*` on postgres-memory) is the fastest read path for analytics; `mcp__github__list_issues` / `mcp__github__projects_get` are the authoritative live path if the mirror looks stale — check `curl -s http://localhost:8090/api/sync/status | jq .is_stale` (or `SELECT max(completed_at) FROM jira.sync_metadata WHERE status='completed'`). Do NOT judge staleness by `max(synced_at)` on `jira.issues` — since LAB-1007 the hourly reconcile skips unchanged rows, so `synced_at` legitimately stands still through webhook-quiet hours.

2. **Query open work by board Status** (mirror SQL — filter `gh_repo` when scoped):
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT gh_repo, status, count(*) FROM jira.issues
      WHERE status_category <> 'Done' GROUP BY 1, 2 ORDER BY 1, 2;"
   ```
   And the In Progress detail:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT issue_key, summary, assigned_agent, updated_at::date FROM jira.issues
      WHERE status = 'In Progress' ORDER BY updated_at DESC;"
   ```

3. **Query the blocked set** (`issue_links`: `source_key` = blocker, `target_key` = blocked):
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT b.issue_key, b.summary, l.source_key AS blocked_by, s.status AS blocker_status
      FROM jira.issue_links l
      JOIN jira.issues b ON b.issue_key = l.target_key
      JOIN jira.issues s ON s.issue_key = l.source_key
      WHERE l.link_type = 'Blocks'
        AND b.status_category <> 'Done'
        AND s.status_category <> 'Done'
      ORDER BY b.issue_key;"
   ```

4. **Compute next-eligible issues** (work queue = Backlog + Planned + not Blocked):
   a. Candidates — Backlog with acceptance criteria and no open blockers:
      ```bash
      docker exec postgres-memory psql -U postgres -d agent_memory -c \
        "SELECT i.issue_key, i.summary, i.priority FROM jira.issues i
         WHERE i.status = 'Backlog'
           AND i.description_text ILIKE '%acceptance criteria%'
           AND NOT EXISTS (
             SELECT 1 FROM jira.issue_links l
             JOIN jira.issues s ON s.issue_key = l.source_key
             WHERE l.link_type = 'Blocks' AND l.target_key = i.issue_key
               AND s.status_category <> 'Done')
         ORDER BY i.priority NULLS LAST, i.created_at;"
      ```
   b. For each candidate, confirm **Planned** with `mcp__github__issue_read` (method `get_comments`): a comment containing `## Implementation Plan` must exist. Note issues with criteria but no plan as "needs planning".
   c. Skip candidates whose latest `Assigned Agent:` comment names another agent.
   d. Collect the eligible set ordered by priority.

5. **Recent completions** (last 7 days):
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT issue_key, summary, resolution, resolved_at::date FROM jira.issues
      WHERE status_category = 'Done' AND resolved_at > now() - interval '7 days'
      ORDER BY resolved_at DESC;"
   ```
   (`resolution` distinguishes Done = closed/completed from Won't Do = closed/not_planned.)

6. **Format overview** — Display a structured summary:

   ```
   ## Project Status: <repo | both repos>

   ### Board: Homelab Work
   | Status | Count |
   |--------|-------|
   | Backlog | X |
   | In Progress | Y |
   | Implementation Complete | Z |
   | Review Complete | W |
   | Deferred | V |

   ### In Progress
   | Key | Summary | Assigned Agent | Updated |
   |-----|---------|----------------|---------|

   ### Blocked (waiting on dependencies)
   | Key | Summary | Blocked By | Blocker Status |
   |-----|---------|-----------|----------------|

   ### Next Eligible (ready for pickup)
   | Key | Summary | Priority | Notes |
   |-----|---------|----------|-------|
   | ... | ...     | High     | No blockers / Just unblocked |

   ### Recently Closed (7 days)
   | Key | Summary | Outcome | Closed |
   |-----|---------|---------|--------|
   ```

7. **Output** — Display the formatted overview. Issue URLs come from the mirror's `jira_url` column if links are needed.

## Required Tools

- `docker exec postgres-memory psql ...` — mirror analytics (read-only; never write to `jira.*`)
- `mcp__github__issue_read` (method `get_comments` — Planned check)
- `mcp__github__list_issues` / `mcp__github__projects_get` — live fallback if the mirror is stale

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
