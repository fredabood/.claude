---
description: Create a structured Jira ticket with acceptance criteria, duplicate detection, and epic linking
user_invocable: true
---

# /create-ticket

Create a well-structured Jira ticket with acceptance criteria, after checking for duplicates.

## Usage

```
/create-ticket "<description>"
/create-ticket "<description>" --epic <EPIC-KEY>
/create-ticket "<description>" --type Bug
```

## Steps

### Step 1: Search for existing tickets

Query Jira for related tickets to avoid duplicates:
```
searchJiraIssuesUsingJql(cloudId, "project = <KEY> AND summary ~ '<keywords>' AND status != Done ORDER BY created DESC")
```

If potential duplicates found, present them and ask the user to confirm this is new work.

### Step 2: Evaluate decomposition

Assess whether the described work should be multiple tickets:

- **Multiple codebase areas:** Independent parts of the system?
- **Independent verification:** Acceptance criteria groupable into independently verifiable sets?
- **Phase boundaries:** Setup/infrastructure separate from feature work?
- **Session scope:** More than one session of effort?
- **Mixed types:** Bugs + features, or infrastructure + user-facing?

If 2+ criteria apply:
1. Present the proposed decomposition: each ticket with summary, type, and which acceptance criteria it carries
2. Ask user to confirm or adjust
3. If confirmed, create each ticket individually (following Steps 3-9 for each)
4. After all created, proceed to dependency linking step

If not warranted, proceed with a single ticket.

### Step 3: Determine ticket type

- **Story** — new user-facing functionality
- **Task** — technical work, infrastructure, refactoring
- **Bug** — something is broken
- **Sub-task** — part of a larger story/task (requires parent)

Infer from the description or ask the user if ambiguous.

### Step 4: Get project metadata

Use `getJiraProjectIssueTypesMetadata` to confirm available issue types and required fields for the target project.

### Step 5: Draft the ticket

Structure the ticket with these sections:

```markdown
**Summary:** <under 80 characters>

## Context
<Why this work is needed — the problem or opportunity>

## Scope
<What specifically will be done>

## Acceptance Criteria
- [ ] <Specific verifiable condition>
- [ ] Tests pass: `<command>`
- [ ] No security regressions
- [ ] Documentation updated (if applicable)

## Out of Scope
<What is explicitly not included>

## Technical Notes
<Implementation hints, relevant files, dependencies>
```

### Step 6: Present for confirmation

Show the draft to the user. Wait for approval before creating.

### Step 7: Create in Jira

Use `createJiraIssue` with the CloudId from CLAUDE.md. Include:
- Summary, description, issue type
- Priority (infer or ask)
- Labels (auto-detect from content: `infrastructure`, `security`, `documentation`, etc.)

### Step 8: Link to parent and dependencies

**Epic link:** If an epic was specified, use `createIssueLink` to link the ticket to the epic.

**Dependency links:** If this ticket depends on or blocks other tickets:
1. Call `getIssueLinkTypes(cloudId)` to discover link types (if not already cached)
2. For each dependency:
   - Blocked by existing ticket: `createIssueLink(cloudId, type: { name: "Blocks" }, outwardIssue: { key: "<EXISTING>" }, inwardIssue: { key: "<NEW>" })`
   - Blocks existing ticket: `createIssueLink(cloudId, type: { name: "Blocks" }, outwardIssue: { key: "<NEW>" }, inwardIssue: { key: "<EXISTING>" })`

**Decomposed tickets:** If multiple tickets were created, create "Blocks" links between them to express ordering (earlier phases block later phases).

### Step 9: Output

Display:
- Ticket key and summary
- Link to the ticket
- Acceptance criteria summary
- Dependency links created: `BLOCKER blocks BLOCKED`

## Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)
- `getJiraProjectIssueTypesMetadata` (cloudId, projectIdOrKey)
- `createJiraIssue` (cloudId, fields)
- `createIssueLink` (cloudId, linkType, inwardIssue, outwardIssue)
- `getIssueLinkTypes` (cloudId)
- `getJiraIssue` (cloudId, issueIdOrKey)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
