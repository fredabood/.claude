# Custom Fields — Jira Field ID Mapping

Canonical mapping of custom field names to Jira `customfield_NNNNN` IDs.
All skills, hooks, and agents reference this file for field operations.

> Created by LAB-628 + LAB-627 via Jira REST API (2026-03-28).

---

## Plan Fields

| Field Name | Field ID | Type |
|-----------|----------|------|
| Plan: Jira Tracking | `customfield_10173` | textarea |
| Plan: Testing Strategy | `customfield_10174` | textarea |
| Plan: Documentation | `customfield_10175` | textarea |
| Plan: Success Criteria | `customfield_10176` | textarea |
| Plan: Risk Assessment | `customfield_10177` | textarea |
| Plan Sections Complete | `customfield_10190` | multicheckboxes |

**Plan Sections Complete options (context 10430):**

| Option | ID |
|--------|-----|
| Jira Tracking | `10130` |
| Testing Strategy | `10131` |
| Documentation | `10132` |
| Success Criteria | `10133` |
| Risk Assessment | `10134` |

## Verification Fields

| Field Name | Field ID | Type |
|-----------|----------|------|
| Verification: Criteria Tested | `customfield_10178` | textarea |
| Verification: Results Summary | `customfield_10179` | textarea |
| Verification Sections Complete | `customfield_10191` | multicheckboxes |

**Verification Sections Complete options (context 10431):**

| Option | ID |
|--------|-----|
| Criteria Tested | `10135` |
| Results Posted | `10136` |
| All Pass | `10137` |

## Post-Mortem Fields

| Field Name | Field ID | Type |
|-----------|----------|------|
| Post-Mortem: What Went Well | `customfield_10180` | textarea |
| Post-Mortem: What Didnt Go Well | `customfield_10181` | textarea |
| Post-Mortem: Lessons Learned | `customfield_10182` | textarea |
| Post-Mortem: Metrics | `customfield_10183` | textarea |
| Post-Mortem: Follow-Up Items | `customfield_10184` | textarea |
| Post-Mortem Sections Complete | `customfield_10192` | multicheckboxes |

**Post-Mortem Sections Complete options (context 10432):**

| Option | ID |
|--------|-----|
| What Went Well | `10138` |
| What Didnt | `10139` |
| Lessons Learned | `10140` |
| Metrics | `10141` |
| Follow-Ups | `10142` |

## Doc Review Fields

| Field Name | Field ID | Type |
|-----------|----------|------|
| Doc Review: Documentation | `customfield_10185` | textarea |
| Doc Review: Memory Updates | `customfield_10186` | textarea |

## Agent Tracking Fields

| Field Name | Field ID | Type |
|-----------|----------|------|
| Primary Agent | `customfield_10188` | textfield |
| Assigned Agent | `customfield_10189` | textfield |
| Agent Runtime | `customfield_10187` | textarea |

## Utility Fields

| Field Name | Field ID | Type |
|-----------|----------|------|
| Workflow Phase | `customfield_10193` | float |

## Success Criterion Fields (SC type only)

| Field Name | Field ID | Type |
|-----------|----------|------|
| Test Marker | `customfield_10194` | textfield |
| Human Approval Required | `customfield_10195` | multicheckboxes |

**Human Approval Required options (context 10435):**

| Option | ID |
|--------|-----|
| Required | `10143` |

---

## Issue Types

| Name | ID | Subtask |
|------|-----|---------|
| Success Criterion | `10222` | true |

## Statuses

| Status | ID | Category | Board Column |
|--------|-----|----------|-------------|
| To Do | `10050` | TODO | To Do |
| In Progress | `10051` | IN_PROGRESS | In Progress |
| Done | `10052` | DONE | Done |
| Implementation Complete | (board-created) | IN_PROGRESS | Own column (transition 81) |
| Review Complete | (board-created) | IN_PROGRESS | Own column (transition 91) |
| Won't Do | (board-created) | DONE | Done column (transition 71) |
| Deferred | `10278` | TODO | Backlog column (transition 101) |

## Transition IDs

**Always use `getTransitionsForJiraIssue` at runtime** to discover transition IDs.
Do not hardcode — transition IDs change when statuses are added to the board.

Known transitions (company-managed LAB project):

| Transition | ID | Target Status | Category |
|-----------|-----|---------------|----------|
| Backlog | `11` | Backlog | To Do |
| Selected for Development | `21` | Selected for Development | To Do |
| In Progress | `31` | In Progress | In Progress |
| Implementation Complete | `81` | Implementation Complete | In Progress |
| Review Complete | `91` | Review Complete | In Progress |
| Done | `41` | Done | Done |
| Won't Do | `71` | Won't Do | Done |
| Deferred | `101` | Deferred | To Do |

Skills should still use `getTransitionsForJiraIssue` at runtime for resilience.

## Issue Type Schemes

| Scheme | ID | Includes SC? |
|--------|-----|-------------|
| LAB: Kanban Issue Type Scheme | `10437` | Yes (added via API) |

---

## Usage

### Reading a field value
```python
issue = getJiraIssue(issueIdOrKey="LAB-XXX")
assigned_agent = issue["fields"].get("customfield_10189")
```

### Writing a field value
```python
editJiraIssue(issueIdOrKey="LAB-XXX", fields={
    "customfield_10189": "claude-session-abc123"  # Assigned Agent
})
```

### Setting a multi-select value
```python
editJiraIssue(issueIdOrKey="LAB-XXX", fields={
    "customfield_10190": [{"id": "10130"}, {"id": "10131"}]  # Plan Sections Complete
})
```
