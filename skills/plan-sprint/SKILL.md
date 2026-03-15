---
description: Sprint planning workflow — analyze state, prioritize work, create actionable sprint plan
user_invocable: true
---

# /plan-sprint

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

- Identify which tickets block others
- Determine what can be parallelized
- Find the critical path (longest sequential chain)

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

### Tickets (ordered by priority)
| Key | Summary | Priority | Estimate | Dependencies |
|-----|---------|----------|----------|-------------|
| ... | ...     | High     | 2d       | None        |

### Milestones
- Week 1: <milestone>
- Week 2: <milestone>

### Risks
- <risk and mitigation>
```

### Step 7: Update Jira

- Create any new tickets identified during planning
- Update priorities and sprint assignments in Jira
- Link dependent tickets

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
