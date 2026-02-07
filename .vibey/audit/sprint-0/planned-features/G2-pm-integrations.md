# G2: PM Tool Integrations Architecture Review

**Task ID:** 01KFXJ78XKT55N2AN8K5P7JY8E
**Phase:** G2: Planned Features
**Date:** 2026-01-29

## Executive Summary

Review of the PM Tool Integrations track (01KCVE6BV6W7FMHB2TPPBCF2EN) covering 11 sprints and 52 tasks, currently 13% complete. The track implements adapters for Jira, GitHub, Trello, Asana, and Confluence with bidirectional sync capabilities. Key finding: Remote mode creates a three-way sync challenge (PM Tool ↔ Local Vibey ↔ Databricks), requiring a central coordinator pattern with conflict resolution.

## Methodology

**Files Analyzed:**
- `.vibey/roadmap/tracks/01KCVE6BV6W7FMHB2TPPBCF2EN.yaml` - Track definition
- `vibey/adapters/pm/*.py` - Existing PM adapter infrastructure

## Findings

### 2. Planned Integrations Table

| PM Tool | Entities Synced | Direction | Status | Track Location |
|---------|-----------------|-----------|--------|----------------|
| Jira | Epic↔Track, Story↔Sprint, Task↔Task | Bidirectional | Planned | Sprint 4-5 |
| GitHub | Issue↔Task, Milestone↔Sprint, Project↔Track | Bidirectional | Planned | Sprint 6 |
| Trello | Board↔Track, List↔Sprint, Card↔Task | Bidirectional | Planned | Sprint 7 |
| Asana | Project↔Track, Section↔Sprint, Task↔Task | Bidirectional | Planned | Sprint 8 |
| Confluence | Page↔Doc, Space↔Track | Export/Link | Planned | Sprint 9 |

### 3. Sync Patterns Table

| Pattern | Trigger | Frequency | Conflict Handling |
|---------|---------|-----------|-------------------|
| Import | Manual CLI command | On-demand | Warn on overwrites |
| Export | Manual CLI command | On-demand | Create new / update |
| Bidirectional | Webhook + polling | Real-time + 5min | Last-write-wins |
| Incremental | Change detection | On change | Merge changes |
| Full Sync | Manual trigger | On-demand | Reconcile all |

### 4. Conflict Resolution Table

| Conflict Type | Detection | Resolution | Manual Override |
|---------------|-----------|------------|-----------------|
| Status Mismatch | Compare timestamps | Latest wins | Yes - force direction |
| Title Change | Hash comparison | PM tool wins | Yes - prefer local |
| Description Change | Hash comparison | Merge if possible | Yes - choose version |
| Assignment Change | Compare timestamps | Latest wins | Yes - prefer PM |
| New Task | Detect by ID absence | Create in target | Yes - skip |
| Deleted Task | Detect by ID missing | Mark deleted | Yes - force delete |

### 5. Data Mapping Table

| PM Tool Entity | Vibey Entity | Field Mapping | Status Mapping |
|----------------|--------------|---------------|----------------|
| Jira Epic | Track | Summary→name, Key→external_id | To Do→not_started, In Progress→in_progress, Done→completed |
| Jira Story | Sprint | Summary→name, Sprint Field→sprint_id | Same as Epic |
| Jira Task | Task | Summary→title, Description→description | Same as Epic |
| GitHub Issue | Task | Title→title, Body→description | Open→not_started, Closed→completed |
| GitHub Milestone | Sprint | Title→name, Description→description | Open→in_progress, Closed→completed |
| Trello Card | Task | Name→title, Desc→description | List position→status |
| Asana Task | Task | Name→title, Notes→description | Not Started→not_started, Completed→completed |

### 6. Remote Mode Architecture

| Flow | PM Tool | Local Vibey | Remote Databricks | Orchestrator |
|------|---------|-------------|-------------------|--------------|
| Import | Source | Destination | Sync target | Local CLI |
| Export | Destination | Source | Source | Local CLI |
| Bidirectional | Peer | Peer | Central | Databricks |
| Webhook | Sender | - | Receiver | Databricks |
| Polling | Target | Agent | Scheduler | Databricks |

**Three-Way Sync Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THREE-WAY PM SYNC ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘

  PM TOOLS                   LOCAL VIBEY                   DATABRICKS
  ─────────                  ───────────                   ──────────

┌─────────────────┐                                   ┌─────────────────┐
│ Jira            │◀────────── Adapter ─────────────▶│ Central State   │
├─────────────────┤         (bidirectional)          │ (Delta Lake)    │
│ GitHub          │                                   │                 │
├─────────────────┤       ┌─────────────────┐         │ Tracks          │
│ Trello          │◀─────▶│ Local Roadmap   │◀───────▶│ Sprints         │
├─────────────────┤       │ (.vibey/)       │         │ Tasks           │
│ Asana           │       └─────────────────┘         │                 │
├─────────────────┤              │                    │ Sync Log        │
│ Confluence      │              │                    │ Conflicts       │
└─────────────────┘              │                    └────────┬────────┘
         │                       │                             │
         │                       │                             │
         └───────────────────────┴─────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │ Coordinator     │
                   │ (resolve order) │
                   │ PM → DB → Local │
                   └─────────────────┘
```

### 7. Credential Management Table

| PM Tool | Auth Method | Storage | Refresh Strategy |
|---------|-------------|---------|------------------|
| Jira Cloud | OAuth 2.0 | Keyring / Secrets | Auto-refresh |
| Jira Server | API Token | Keyring / Secrets | Manual rotation |
| GitHub | Personal Access Token | Keyring / Secrets | Manual rotation |
| Trello | API Key + Token | Keyring / Secrets | Manual rotation |
| Asana | Personal Access Token | Keyring / Secrets | Manual rotation |
| Confluence | API Token | Keyring / Secrets | Manual rotation |

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| 5 PM tools planned | Prioritize Jira + GitHub | L | High |
| Bidirectional sync complex | Use central coordinator | M | Critical |
| Webhooks need endpoint | Databricks REST endpoint | M | High |
| Credentials are local | Use Databricks Secrets | S | High |
| 11 sprints of work | Can parallelize adapters | - | Medium |
| Confluence is export-only | Lower priority | S | Low |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Planned integrations table lists >= 3 PM tools: PASS (5 tools)
- [x] Sync patterns table covers bidirectional sync: PASS
- [x] Remote mode architecture shows three-way flow: PASS
- [x] Data mapping table includes status mapping: PASS

## References

- `.vibey/roadmap/tracks/01KCVE6BV6W7FMHB2TPPBCF2EN.yaml:1-102` - Track definition
- Track progress: 13% complete, 11 sprints, 52 tasks
- `vibey/adapters/pm/` - Existing PM adapter infrastructure
