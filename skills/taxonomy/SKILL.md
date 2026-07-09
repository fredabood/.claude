---
description: Audit, report, and manage taxonomy labels across the homelab and dirtydata repos
user_invocable: true
---

# /taxonomy

**Before any GitHub issue operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "taxonomy", "started_at": "<current ISO8601 timestamp>", "ticket_key": null}`

Audit, report, and manage work taxonomy labels across **both repos**: `fredabood/homelab` and `fredabood/dirtydata`. The label taxonomy (7 work patterns + 4 layers, per `.claude/rules/label-taxonomy.md`) exists identically in both repos.

The postgres mirror (`jira.*`, read-only) is the fast path for label analytics — `labels` is a `text[]` column. Label mutations go through GitHub (`mcp__github__issue_write` or `gh issue edit` / `gh label`).

## Usage

```
/taxonomy             — overview with counts by pattern, layer, and status
/taxonomy audit       — find missing labels, label parity drift, dependency violations, and status violations
/taxonomy apply <KEY> — interactively classify a specific issue (HL-<n>, DD-<n>, or migrated LAB-*/DRTY-*)
/taxonomy report      — cross-repo dependency report by layer
/taxonomy queue       — agent work queue diagnostics (Planned+Unblocked)
```

## Steps

### Step 1: `/taxonomy` — Overview

Display taxonomy coverage across both repos (exclude epics — the mirror marks issues with sub-issues as `issue_type = 'Epic'`).

1. Pattern × layer cross-tabulation from the mirror:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT p.pattern, l.layer, count(*)
      FROM jira.issues i,
           LATERAL unnest(i.labels) p(pattern),
           LATERAL unnest(i.labels) l(layer)
      WHERE i.issue_type <> 'Epic'
        AND p.pattern IN ('scraper','agent','workflow','deployment','pipeline','migration','platform')
        AND l.layer IN ('L1-platform','L2-services','L3-framework','L4-domain')
      GROUP BY 1, 2 ORDER BY 1, 2;"
   ```
2. Unlabeled / partially labeled counts:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT gh_repo,
        count(*) FILTER (WHERE NOT labels && ARRAY['scraper','agent','workflow','deployment','pipeline','migration','platform']) AS missing_pattern,
        count(*) FILTER (WHERE NOT labels && ARRAY['L1-platform','L2-services','L3-framework','L4-domain']) AS missing_layer,
        count(*) AS total
      FROM jira.issues WHERE issue_type <> 'Epic' GROUP BY 1;"
   ```
3. Display the matrix (pattern rows × layer columns) plus summary: total issues, labeled count, unlabeled count, coverage percentage
4. Status distribution across the workflow (board Status for open, close reason for terminal):
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT status, count(*) FROM jira.issues WHERE issue_type <> 'Epic' GROUP BY 1 ORDER BY 2 DESC;"
   ```
   Display counts for: Backlog, In Progress, Implementation Complete, Review Complete, Deferred, Done (closed/completed), Won't Do (closed/not_planned)
5. Show Planned/Blocked summary for Backlog issues:
   - Candidates: `status = 'Backlog' AND description_text ILIKE '%acceptance criteria%'` (mirror)
   - For each, check plan comment (`## Implementation Plan` via `mcp__github__issue_read` method `get_comments`) and open blockers (mirror `issue_links` or `gh api .../dependencies/blocked_by`)
   - Report: X Planned+Unblocked (ready for pickup), Y Planned+Blocked, Z Unplanned

### Step 2: `/taxonomy audit` — Find violations

Identify issues that violate taxonomy rules.

**Missing labels:**
1. Issues with no labels at all, and issues missing a taxonomy dimension:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT gh_repo, issue_key, summary, labels FROM jira.issues
      WHERE issue_type <> 'Epic' AND status_category <> 'Done'
        AND (NOT labels && ARRAY['scraper','agent','workflow','deployment','pipeline','migration','platform']
          OR NOT labels && ARRAY['L1-platform','L2-services','L3-framework','L4-domain'])
      ORDER BY gh_repo, issue_key;"
   ```
2. Issues with **more than one** label in a dimension (rule: exactly one each) — flag for cleanup.

**Label parity between repos:**
3. The taxonomy label set must exist identically in both repos. Compare:
   ```bash
   diff <(gh label list -R fredabood/homelab --json name --jq '.[].name' | sort) \
        <(gh label list -R fredabood/dirtydata --json name --jq '.[].name' | sort)
   ```
   For missing taxonomy labels, offer to create them: `gh label create <name> -R fredabood/<repo> --color <hex> --description "<desc>"` (copy color/description from the repo that has it).

**Dependency direction violations:**
4. Blocks links from the mirror (`source_key` = blocker, `target_key` = blocked); read both sides' layer labels
5. Flag if the blocker's layer number > the blocked issue's layer number (e.g., L4 blocking L1):
   `VIOLATION: <blocker_key> (L4) blocks <blocked_key> (L1) — dependencies must flow L1→L4`

**Status dimension violations:**
6. Issues "In Progress" with no assignment (stale/orphaned): for each `status = 'In Progress'` issue, look for the latest `Assigned Agent:` comment (`issue_read` method `get_comments`; migrated issues may have the mirror's `assigned_agent` column) — flag if none.
7. Issues in "Implementation Complete" without a verification report: search comments for `## Verification Report` — flag if missing.
8. Planned+Unblocked issues sitting in Backlog (ready but not started):
   Report as positive signal: "N issues ready for agent pickup"

**Output:** violations grouped by type (missing labels, label parity drift, upward dependencies, status violations), with issue keys and suggested fixes.

### Step 3: `/taxonomy apply <KEY>` — Classify an issue

Interactively add taxonomy labels to a specific issue.

1. Resolve `<KEY>` to repo/number (`HL-<n>` → homelab#n, `DD-<n>` → dirtydata#n; migrated keys via `SELECT gh_repo, gh_number FROM jira.issues WHERE issue_key = '<KEY>'`)
2. `mcp__github__issue_read` (method `get`) — read current labels, title, body
3. Detect work pattern from title/body keywords (per `.claude/rules/label-taxonomy.md` keyword hints)
4. Infer infrastructure layer:
   - dirtydata domain business logic → `L4-domain`
   - homelab → infer L1/L2/L3 from content (L4 for consolidated domain epics)
5. Present: "Proposed labels: **{pattern}** / **{layer}**. Correct?"
6. On confirmation, apply — preserve existing non-taxonomy labels, add pattern + layer:
   `mcp__github__issue_write` (update labels) or `gh issue edit <n> -R fredabood/<repo> --add-label "<pattern>,<layer>"`
7. Display the updated issue with new labels

### Step 4: `/taxonomy report` — Cross-repo dependency report

Show how infrastructure issues relate to domain work across layers and repos.

1. Query Blocks links with both endpoints' repos and layer labels:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT l.source_key AS blocker, bs.gh_repo AS blocker_repo, bs.labels AS blocker_labels,
             l.target_key AS blocked, bt.gh_repo AS blocked_repo, bt.labels AS blocked_labels
      FROM jira.issue_links l
      JOIN jira.issues bs ON bs.issue_key = l.source_key
      JOIN jira.issues bt ON bt.issue_key = l.target_key
      WHERE l.link_type = 'Blocks' AND bt.status_category <> 'Done';"
   ```
2. Group by blocker layer → blocked repo/issue:
   ```
   L1-platform:
     HL-XX (Docker networking) → blocks DD-YY
   L2-services:
     HL-XX (PostgreSQL) → blocks DD-YY
   L3-framework:
     HL-XX (scraper framework) → blocks DD-YY, HL-ZZ
   ```
3. Flag any links flowing upward (higher layer blocking lower layer)
4. Show summary counts: total cross-repo links, by layer, violations

### Step 5: `/taxonomy queue` — Agent work queue diagnostics

Display the current Planned+Unblocked work queue with diagnostics.
See `.claude/rules/label-taxonomy.md` for canonical definitions of Planned, Blocked, and the agent work queue.

1. Query Backlog issues with acceptance criteria (mirror):
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "SELECT issue_key, summary, priority, labels FROM jira.issues
      WHERE status = 'Backlog' AND issue_type <> 'Epic'
        AND description_text ILIKE '%acceptance criteria%'
      ORDER BY priority NULLS LAST, created_at;"
   ```
2. For each issue, compute:
   - **Planned:** acceptance criteria task list in the body AND a `## Implementation Plan` comment exists (`issue_read` method `get_comments`)
   - **Blocked:** any open blocker (mirror `issue_links` where `target_key = <key>` and blocker `status_category <> 'Done'`, or `gh api .../dependencies/blocked_by`)
   - **Primary Agent:** derive from work pattern label → agent routing table in label-taxonomy.md
3. Display queue table:
   ```
   | Key | Summary | Pattern | Layer | Planned | Blocked | Primary Agent |
   ```
4. Highlight eligible items (Planned=true, Blocked=false) as "Ready for pickup"
5. For blocked items, show blocker chain: "HL-XXX blocked by HL-YYY (In Progress)"
6. Summary: "N eligible for pickup, M blocked, P need planning"

**Note:** Planned/Blocked are calculated agent-side from body, comments, and dependency links — there are no stored fields. Values shown are best-effort at read time.

## Required Tools

- `docker exec postgres-memory psql ...` — mirror analytics (read-only; never write to `jira.*`)
- `mcp__github__issue_read` (methods `get`, `get_comments`, `get_labels`)
- `mcp__github__issue_write` (label updates)
- `gh label list` / `gh label create` / `gh issue edit` — repo label ops
- `gh api .../dependencies/blocked_by` — authoritative blocker readback

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
