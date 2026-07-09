Query the work queue for the next eligible issues (Status=Backlog, Planned, not Blocked).

1. Get the candidate set from the postgres mirror (read-only) — open issues in Backlog
   with no unresolved blocker (`issue_links`: `source_key` = blocker, `target_key` = blocked):

   ```
   docker exec postgres-memory psql -U postgres -d agent_memory -c "
   SELECT i.issue_key, i.summary, i.priority, i.labels, i.gh_repo, i.gh_number
   FROM jira.issues i
   WHERE i.status = 'Backlog'
     AND NOT EXISTS (
       SELECT 1 FROM jira.issue_links l
       JOIN jira.issues k ON k.issue_key = l.source_key
       WHERE l.link_type = 'Blocks' AND l.target_key = i.issue_key
         AND k.status_category <> 'Done')
   ORDER BY i.priority, i.created_at
   LIMIT 15"
   ```

2. For each candidate (up to 10), verify it is **Planned** via `mcp__github__issue_read`
   (owner `fredabood`, repo/number from `gh_repo`/`gh_number`):
   - method `get` → body contains an `## Acceptance Criteria` task list
   - method `get_comments` → a comment contains `## Implementation Plan`
3. Skip candidates whose latest `Assigned Agent:` comment names another active agent.
4. Present the top 3 eligible issues as a prioritized list: key, summary, priority, and a
   1-sentence description.

If no eligible issues exist, report: (a) Backlog issues missing criteria or a plan comment
(what's missing for each), and (b) which blockers need resolving to unlock the next tier
(re-run the mirror query without the NOT EXISTS filter and show the blocking chains).
