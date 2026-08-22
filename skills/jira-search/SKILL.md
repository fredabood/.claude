---
name: jira-search
description: "Search GitHub issues across the homelab and dirtydata repos and display results as a formatted table"
user_invocable: true
---

# /jira-search

Search issues and display results in a readable table format. (Directory name kept as
`jira-search` for invocation compatibility — the tracker is GitHub Issues; the postgres
mirror retains the `jira.*` schema name.)

## Usage

```
/jira-search
/jira-search <query>
```

Examples:
- `/jira-search state:open label:platform` — raw GitHub qualifiers, passed through
- `/jira-search open deployment issues in dirtydata` — natural language, mapped to qualifiers
- `/jira-search how many issues closed per month this year` — analytical, answered via mirror SQL

## Steps

1. **Write skill execution context marker:** Run: `bash "$CLAUDE_PROJECT_DIR/.claude/hooks/lib/skill-marker.sh" set jira-search`

2. **Choose the backend:**
   - **Listing/filtering searches** → `mcp__github__search_issues`
   - **Analytical queries** (counts, aggregates, date math, joins across links/changelog, board-status filters, migrated-key lookups) → mirror SQL:
     `docker exec postgres-memory psql -U postgres -d agent_memory` (READ ONLY — never write to `jira.*`)

3. **Map the request to search qualifiers** (JQL is gone — translate JQL-ish requests):

   | Old JQL idiom | GitHub qualifier |
   |---------------|------------------|
   | `project = LAB` | `repo:fredabood/homelab` |
   | `project = DRTY` | `repo:fredabood/dirtydata` |
   | `status = "To Do"` / open categories | `state:open` (board Status needs `projects_get` or mirror SQL) |
   | `statusCategory = Done` | `state:closed` |
   | `status = "Won't Do"` | `state:closed reason:not-planned` |
   | `labels = platform` | `label:platform` |
   | `text ~ "foo"` | bare terms `foo in:title,body` |
   | `assignee = X` | `assignee:X` |
   | `created >= -7d` | `created:>=<YYYY-MM-DD>` |
   | `ORDER BY updated DESC` | `sort:updated-desc` |

   Default query when none provided: `repo:fredabood/homelab state:open sort:updated-desc`.
   If no `repo:` qualifier is implied, search both repos (`repo:fredabood/homelab repo:fredabood/dirtydata` is not OR'd by GitHub — run two searches or use `user:fredabood`).

   **Board-status filtering** (e.g. "In Progress") is not a search qualifier — filter open
   results by board Status via `mcp__github__projects_get`, or go straight to mirror SQL:

   ```sql
   SELECT issue_key, summary, status, labels, updated_at
   FROM jira.issues
   WHERE status = 'In Progress'
   ORDER BY updated_at DESC LIMIT 20;
   ```

4. **Execute** with `mcp__github__search_issues` (query, owner/repo as appropriate), cap at 20 results — or run the mirror SQL.

5. **Format results** as a markdown table:

   ```
   ## Issue Search Results

   **Query:** `<query>`
   **Results:** X issues found

   | Key | Summary | State/Status | Labels | Updated |
   |-----|---------|--------------|--------|---------|
   | LAB-963 | Example issue | In Progress | platform, L3-framework | 2026-07-05 |
   ```

   - Key = mirror key: `LAB-<n>` (homelab) / `DRTY-<n>` (dirtydata) / `RESORT-<n>` (9215resort); post-migration `<n>` = GitHub issue number, migrated issues keep their original `LAB-*`/`DRTY-*`/`LEGACY-*` keys (`jira.gh_issue_key(repo, number)` resolves it; deprecated `HL-*`/`DD-*` ≡ `LAB-*`/`DRTY-*`)
   - If no results, display: "No issues found for this query."
   - Truncate summary to 60 characters if longer, with ellipsis
   - Format updated date as YYYY-MM-DD (date only, no time)
   - Show assignee login if set, or "-" if unassigned

6. **Cleanup:** Run `bash "$CLAUDE_PROJECT_DIR/.claude/hooks/lib/skill-marker.sh" clear`.

## Required tools

- `mcp__github__search_issues` (or `mcp__github__list_issues` for simple repo listings)
- `mcp__github__projects_get` (board Status, when needed)
- `docker exec postgres-memory psql -U postgres -d agent_memory` (analytical queries — READ ONLY)
