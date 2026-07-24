# GitHub Field Mapping — Statuses, Board IDs, and Structured Comments

Canonical mapping of the old Jira field vocabulary to GitHub-native constructs.
All skills, hooks, and agents reference this file for lifecycle operations.

> Rewritten for the GitHub Issues migration (2026-07). The Jira custom fields
> (customfield_10173–10195) are gone; their content lives in **structured issue
> comments** with `##` markers, and workflow status lives on the **Projects v2
> board**. Historical field values are preserved in the postgres mirror columns
> (`jira.issues.plan_*`, `verification_*`, `pm_*`, etc.) for migrated issues.

---

## Projects v2 Board — Stable IDs

| Object | ID |
|--------|-----|
| Project "Homelab Work" (user `fredabood`, number 1) | `PVT_kwHOAM5y1M4BcqrU` |
| `Status` single-select field | `PVTSSF_lAHOAM5y1M4BcqrUzhXRxK4` |

**Status options:**

| Option | ID |
|--------|-----|
| Backlog | `093793f1` |
| In Progress | `62ad3706` |
| Implementation Complete | `2eec8df1` |
| Review Complete | `0aa21637` |
| Deferred | `087e34a4` |

These IDs are stable for the life of the board. Scripts may hardcode them but must
fail loudly if a GraphQL mutation rejects them (board recreated → re-derive with
`gh api graphql` querying `user(login:"fredabood"){projectV2(number:1){...}}`).

## Status Transitions

There are no Jira transition IDs anymore. To move an issue:

| Action | How |
|--------|-----|
| Backlog → In Progress (etc.) | `mcp__github__projects_write` — update item's `Status` field |
| Any → Done | `mcp__github__issue_write` — `state: closed`, `state_reason: completed` |
| Any → Won't Do | `mcp__github__issue_write` — `state: closed`, `state_reason: not_planned` |
| Reopen | `mcp__github__issue_write` — `state: open`, then set board Status |

Closing an issue removes it from the board (D5). Reopening re-adds it via the
webhook receiver with `Status=Backlog`.

## Structured Comment Vocabulary

The old plan/verification/post-mortem custom fields map to issue comments whose
sections use these exact `##`/`###` markers (hooks and the Planned-check grep for them):

### Plan comment (replaces Plan: * fields)

```
## Implementation Plan
### Jira Tracking        → now: Issue Tracking (issues to create, epic membership, dependencies)
### Testing Strategy
### Documentation
### Success Criteria
### Risk Assessment
```

A comment containing `## Implementation Plan` marks the issue as **Planned**
(together with an `## Acceptance Criteria` task list in the body).

### Verification comment (replaces Verification: * fields)

```
## Verification Report
### Criteria Tested      (each body checklist item, individually, with evidence)
### Results Summary
```

### Post-mortem comment (replaces Post-Mortem: * fields)

```
## Post-Mortem: <KEY> — <summary>
### What Went Well
### What Didn't Go Well
### Lessons Learned
### Metrics
### Follow-Up Items
```

### Doc review (replaces Doc Review: * fields)

Folded into the post-mortem or a standalone comment:

```
## Doc Review
### Documentation        (docs/ files created/updated and why)
### Memory Updates       (auto-memory + vault notes persisted)
```

### Agent assignment (replaces Primary/Assigned Agent fields)

```
Assigned Agent: <session-identifier>
Session: <ISO timestamp>
```

Posted as a short comment when picking up an issue. The most recent assignment
comment wins. Warn before overriding another agent's assignment.

## Acceptance Criteria / Success Criterion Issues

- Acceptance criteria = native task list (`- [ ]`) under `## Acceptance Criteria` in the issue **body** (not a comment — the body is editable and renders progress).
- The old Success Criterion subtask type is gone. If a criterion needs standalone tracking, convert the task-list item to a sub-issue (GitHub UI or `sub_issue_write`).
- Test Marker / Human Approval Required: prepend to the criterion text, e.g. `- [ ] [pytest:test_foo] [HUMAN-APPROVAL] <condition>`.

## Issue Types

GitHub's native issue types are an **organization** feature; `fredabood` is a personal
account, so there are **no issue types**. A **parent issue** is simply an issue that has
sub-issues (GitHub's native parent-issue role) — there is no "Epic". Defects use the
`bug` label. The mirror's legacy `issue_type='Epic'` derivation is **deprecated** (detect
parent issues via has-sub-issues); `Relates` links are dropped — GitHub has no native
"relates to", only **blocked by** / **blocking** dependencies.

## Mirror Columns (read-only reference)

For migrated issues, historical field content is preserved in
`jira.issues`: `plan_jira_tracking`, `plan_testing_strategy`, `plan_documentation`,
`plan_success_criteria`, `plan_risk_assessment`, `verification_criteria_tested`,
`verification_results_summary`, `pm_*`, `doc_review_*`, `primary_agent`,
`assigned_agent`, `agent_runtime`, `workflow_phase`, `test_marker`,
`human_approval_required`. New (post-migration) issues have these NULL — their
equivalents are the structured comments above, fetched via
`mcp__github__issue_read` (method `get_comments`).

## Usage

### Reading lifecycle state

```
mcp__github__issue_read  method=get           → state, state_reason, labels, body (criteria)
mcp__github__issue_read  method=get_comments  → plan / verification / post-mortem / assignment
mcp__github__projects_get                     → board Status for open issues
```

### Writing

```
mcp__github__issue_write                      → create/update/close (state_reason!)
mcp__github__add_issue_comment                → structured comments
mcp__github__projects_write                   → board Status
mcp__github__sub_issue_write                  → epic membership
gh api .../dependencies/blocked_by            → Blocks links (no MCP tool yet)
```
