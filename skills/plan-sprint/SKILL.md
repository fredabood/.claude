---
description: Sprint planning workflow — analyze state, prioritize work, create actionable sprint plan
user_invocable: true
---

# /plan-sprint

**Before any Jira operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "plan-sprint", "started_at": "<current ISO8601 timestamp>", "ticket_key": null}`

Run a structured sprint planning process that analyzes current project state, gathers requirements, and produces an actionable sprint plan.

## Usage

```
/plan-sprint
/plan-sprint <PROJECT-KEY>
```

## Steps

### Step 1: Analyze Current State

- Review CLAUDE.md for project context and conventions
- Check `git log --oneline -20` for recent development activity
- Query Jira for current sprint status:
  ```
  project = <KEY> AND sprint in openSprints()
  ```
- Identify what's done, what's in progress, what's blocked

### Step 2: Gather Requirements

- Query Jira backlog:
  ```
  project = <KEY> AND status = "To Do" ORDER BY priority DESC
  ```
- Identify any epics with remaining work:
  ```
  project = <KEY> AND type = Epic AND status != Done
  ```
- Ask the user about priorities, deadlines, or new requirements

### Step 3: Assess Technical Feasibility

- For each candidate item, consider:
  - Is the approach clear or does it need research?
  - Are there dependencies on other tickets?
  - Are there infrastructure or access requirements?
- Flag high-risk items that need spikes or prototypes

### Step 4: Map Dependencies

#### 4a: Discover link types
Call `getIssueLinkTypes(cloudId)` to discover available types. Identify the "Blocks" type.

#### 4b: Audit existing links
For each candidate ticket, call `getJiraIssue(cloudId, issueKey)` and inspect `issuelinks`. Record existing "blocks"/"is blocked by" relationships. Flag circular dependencies as errors.

#### 4c: Identify missing dependencies
Based on the feasibility assessment in Step 3, identify tickets that should have dependency links but don't. Create each:
```
createIssueLink(cloudId, type: { name: "Blocks" },
  inwardIssue: { key: "<BLOCKER>" },
  outwardIssue: { key: "<BLOCKED>" })
```

#### 4d: Build dependency graph
Document the full graph:
```
KEY-1 blocks KEY-2 — <reason>
KEY-3 (no dependencies)
```

#### 4e: Critical path
Identify the longest sequential chain. This determines minimum elapsed time.
```
Critical path: KEY-1 → KEY-2 → KEY-5 (3 tickets)
Parallelizable: KEY-3, KEY-4 (can start immediately)
```

#### 4f: Next-eligible tickets
From the sprint backlog, identify To Do tickets where all "is blocked by" links are Done (or no blockers). These can start immediately.

### Step 5: Prioritize

Score each item using Value / Effort / Risk:

- **Value (1-5):** Business impact, user value
- **Effort (1-5):** Time and complexity
- **Risk (1-5):** Unknowns, technical risk

**Priority = (Value x 2) - (Effort + Risk)**
- High priority: score >= 5
- Medium priority: score 2-4
- Low priority: score <= 1

### Step 6: Create Sprint Plan

Produce a structured plan:

```markdown
## Sprint Plan: <Sprint Name>
**Duration:** <X weeks>
**Goal:** <one-line sprint goal>

### Definition of Done
- All acceptance criteria verified with evidence
- Tests pass (unit + integration)
- No security regressions
- Documentation updated where applicable
- Post-mortem posted to ticket
- Code reviewed

### Tickets (ordered by priority)
| Key | Summary | Priority | Estimate | Dependencies | Criteria Status |
|-----|---------|----------|----------|-------------|-----------------|
| ... | ...     | High     | 2d       | None        | Has criteria / Needs criteria |

### Milestones
- Week 1: <milestone>
- Week 2: <milestone>

### Dependency Graph
KEY-1 blocks KEY-2 — <reason>
...

### Critical Path
KEY-X → KEY-Y → KEY-Z (N sequential tickets)

### Next Eligible (ready to start)
| Key | Summary | Priority | Notes |
|-----|---------|----------|-------|
| ... | ...     | High     | No blockers / Just unblocked |

### Risks
- <risk and mitigation>
```

**Acceptance criteria enforcement:** For any backlog item lacking acceptance criteria, draft them during planning and update the Jira ticket using `addCommentToJiraIssue` or `editJiraIssue`.

### Step 7: Update Jira

- Create any new tickets identified during planning
- Update priorities and sprint assignments in Jira
- Link dependent tickets
- Ensure all planned tickets have acceptance criteria

### Step 8: Update CLAUDE.md

- Update the project's CLAUDE.md with current sprint focus
- Document any new conventions or decisions

### Step 9: Commit Planning Artifacts

- Commit any documentation changes
- Include sprint plan reference in commit message

## Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)
- `createJiraIssue` (cloudId, fields)
- `editJiraIssue` (cloudId, issueIdOrKey, fields)
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `getJiraIssue` (cloudId, issueIdOrKey)
- `createIssueLink` (cloudId, linkType, inwardIssue, outwardIssue)
- `getIssueLinkTypes` (cloudId)

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
