---
description: Audit, report, and manage taxonomy labels across Jira projects
user_invocable: true
---

# /taxonomy

Audit, report, and manage work taxonomy labels across all Jira projects.

## Usage

```
/taxonomy             — overview with counts by pattern and layer
/taxonomy audit       — find missing labels and dependency violations
/taxonomy apply <KEY> — interactively classify a specific ticket
/taxonomy report      — cross-project dependency report by layer
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

**Output:** violations grouped by type (missing labels, upward dependencies), with ticket keys and suggested fixes.

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

## Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)
- `getJiraIssue` (cloudId, issueIdOrKey)
- `editJiraIssue` (cloudId, issueIdOrKey, fields)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
