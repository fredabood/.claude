Surface all open issues that are currently blocked by an unresolved blocker.

1. Query the postgres mirror (read-only) for active blocking relationships — in
   `jira.issue_links`, `source_key` = blocker, `target_key` = blocked:

   ```
   docker exec postgres-memory psql -U postgres -d agent_memory -c "
   SELECT l.target_key AS blocked, b.summary AS blocked_summary, b.status AS blocked_status,
          l.source_key AS blocker, k.status AS blocker_status, k.summary AS blocker_summary
   FROM jira.issue_links l
   JOIN jira.issues b ON b.issue_key = l.target_key
   JOIN jira.issues k ON k.issue_key = l.source_key
   WHERE l.link_type = 'Blocks'
     AND b.status_category <> 'Done'
     AND k.status_category <> 'Done'
   ORDER BY l.target_key"
   ```

2. Optionally spot-verify against GitHub for anything surprising (mirror lags webhook CDC by ~2s):
   `gh api repos/fredabood/<repo>/issues/<n>/dependencies/blocked_by -H "X-GitHub-Api-Version: 2026-03-10"`
   (resolve repo/number: HL-<n> → fredabood/homelab #n, DD-<n> → fredabood/dirtydata #n; migrated keys via `gh_repo`/`gh_number` columns on `jira.issues`)
3. Present a table: blocked issue | blocker issue | blocker status | blocker summary

Only show issues with active (unresolved) blockers. If none, confirm the board is clear.
