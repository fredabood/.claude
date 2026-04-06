---
description: Audit, report, and manage taxonomy labels across Jira projects
user_invocable: true
---

# /taxonomy

**Before any Jira operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "taxonomy", "started_at": "<current ISO8601 timestamp>", "ticket_key": null}`

Audit, report, and manage work taxonomy labels across all Jira projects.

## Usage

```
/taxonomy             — overview with counts by pattern, layer, and status
/taxonomy audit       — find missing labels, dependency violations, and status violations
/taxonomy apply <KEY> — interactively classify a specific ticket
/taxonomy report      — cross-project dependency report by layer
/taxonomy queue       — agent work queue diagnostics (Planned+Unblocked)
```

## Steps

### Step 1: `/taxonomy` — Overview

Display taxonomy coverage across all projects.

1. For each work pattern, query ticket count:
   ```
   labels = "<pattern>" AND issuetype != Epic
   ```
2. For each infrastructure layer, query ticket count:
   ```
   labels = "<layer>" AND issuetype != Epic
   ```
3. Display cross-tabulation matrix (pattern rows x layer columns)
4. Query unlabeled: `issuetype != Epic AND labels is EMPTY`
5. Show summary: total tickets, labeled count, unlabeled count, coverage percentage
6. Query status distribution across the 5-status workflow:
   ```
   status = "<status>" AND issuetype != Epic
   ```
   Display counts for: To Do, In Progress, Work Complete, Doc Review Complete, Won't Do
7. Show Planned/Blocked summary for To Do tickets:
   - Query: `status = "To Do" AND description ~ "Acceptance Criteria" AND issuetype != Epic`
   - For each, check if plan comment exists and if blockers are resolved
   - Report: X Planned+Unblocked (ready for pickup), Y Planned+Blocked, Z Unplanned

### Step 2: `/taxonomy audit` — Find violations

Identify tickets that violate taxonomy rules.

**Missing labels:**
1. Find tickets with no labels at all:
   ```
   issuetype != Epic AND labels is EMPTY ORDER BY project ASC
   ```
2. Find tickets with labels but missing taxonomy dimensions:
   ```
   issuetype != Epic AND NOT (labels in (scraper, agent, workflow, deployment, pipeline, migration, platform)) ORDER BY project ASC
   ```

**Dependency direction violations:**
3. For each project with cross-project Blocks links, use `getJiraIssue` to inspect issuelinks
4. For each Blocks link where the blocker and blocked are in different projects:
   - Read both tickets' layer labels
   - Flag if blocker's layer number > blocked's layer number (e.g., L4 blocking L1)
5. Report: `VIOLATION: {blocker_key} (L4) blocks {blocked_key} (L1) — dependencies must flow L1→L4`

**Status dimension violations:**
6. Find tickets "In Progress" with no Assigned Agent (stale/orphaned):
   ```
   status = "In Progress" AND issuetype != Epic
   ```
   For each, inspect for Assigned Agent — flag if no assignment comment or field.
7. Find tickets "Work Complete" without a verification report:
   ```
   status = "Work Complete" AND issuetype != Epic
   ```
   For each, search comments for verification report — flag if missing.
8. Find Planned+Unblocked tickets sitting in "To Do" (ready but not started):
   Report as positive signal: "N tickets ready for agent pickup"

**Output:** violations grouped by type (missing labels, upward dependencies, status violations), with ticket keys and suggested fixes.

### Step 3: `/taxonomy apply <KEY>` — Classify a ticket

Interactively add taxonomy labels to a specific ticket.

1. `getJiraIssue(cloudId, KEY)` — read current labels, summary, description
2. Detect work pattern from summary keywords (per `.claude/rules/label-taxonomy.md` keyword hints)
3. Infer infrastructure layer:
   - Domain projects (REAL, COS, GAME, HOME, FOOD, WEB) → `L4-domain`
   - LAB → infer L1/L2/L3 from content
4. Present: "Proposed labels: **{pattern}** / **{layer}**. Correct?"
5. On confirmation, apply via `editJiraIssue`:
   - Preserve existing non-taxonomy labels
   - Add work pattern + layer labels
6. Display updated ticket with new labels

### Step 4: `/taxonomy report` — Cross-project dependency report

Show how LAB infrastructure tickets relate to domain project tickets.

1. Query LAB tickets that block other projects:
   ```
   project = LAB AND issuetype != Epic AND issuelinks is not EMPTY
   ```
2. For each, inspect issuelinks for outward "blocks" links to non-LAB tickets
3. Group by blocker layer → blocked project:
   ```
   L1-platform:
     LAB-XX (Docker networking) → blocks GAME-YY, COS-ZZ
   L2-services:
     LAB-XX (PostgreSQL) → blocks REAL-YY
   L3-framework:
     LAB-XX (scraper framework) → blocks REAL-YY, COS-ZZ
   ```
4. Flag any links flowing upward (domain blocking platform)
5. Show summary counts: total cross-project links, by layer, violations

### Step 5: `/taxonomy queue` — Agent work queue diagnostics

Display the current Planned+Unblocked work queue with diagnostics.
See `.claude/rules/label-taxonomy.md` for canonical definitions of Planned, Blocked, and the agent work queue.

1. Query To Do tickets with acceptance criteria:
   ```
   project = LAB AND status = "To Do" AND description ~ "Acceptance Criteria"
     ORDER BY priority DESC, created ASC
   ```
2. For each ticket, use `getJiraIssue` and compute:
   - **Planned:** Acceptance criteria present in description AND plan comment exists in comments
   - **Blocked:** Any unresolved inward "Blocks" link (blocker not in status category "Done")
   - **Primary Agent:** Derive from work pattern label → agent routing table in label-taxonomy.md
3. Display queue table:
   ```
   | Key | Summary | Pattern | Layer | Planned | Blocked | Primary Agent |
   ```
4. Highlight eligible items (Planned=true, Blocked=false) as "Ready for pickup"
5. For blocked items, show blocker chain: "LAB-XXX blocked by LAB-YYY (In Progress)"
6. Summary: "N eligible for pickup, M blocked, P need planning"

**Note:** Until LAB-628 creates custom fields, Planned/Blocked are calculated agent-side from description, comments, and issuelinks. Values shown are best-effort estimates.

## Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)
- `getJiraIssue` (cloudId, issueIdOrKey)
- `editJiraIssue` (cloudId, issueIdOrKey, fields)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
