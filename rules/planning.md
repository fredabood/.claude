---
description: Planning mode behavior — every plan must include Jira tracking, testing strategy, documentation plan, success criteria, and risk assessment
globs:
  - "**/*"
---

# Planning — Structured Design Requirements

When asked to plan, design, or architect a solution, the plan **must** include all five sections below. Plans are not just conversation output — they are posted to the relevant Jira ticket.

## Required plan sections

### 1. Jira Tracking Plan

#### Decomposition evaluation

Before creating tickets, evaluate whether the work should be decomposed:

- **Multiple codebase areas:** Does the work touch independent parts of the system?
- **Independent acceptance criteria:** Can groups of criteria be verified in isolation?
- **Phase boundaries:** Is there a natural split between setup/infrastructure and feature work?
- **Session scope:** Would the work take more than one session?
- **Mixed types:** Does it include both bug fixes and features, or both infrastructure and user-facing changes?

If two or more apply, decompose into multiple tickets. Use sub-tasks when pieces are parts of one story; independent linked tickets when each has standalone value.

#### Ticket structure

- What tickets to create (with type: Story / Task / Bug / Sub-task)
- How they relate to existing epics
- Sprint assignment (if applicable)

#### Dependency mapping

For each pair of tickets where one must complete before another can start:

1. Call `getIssueLinkTypes(cloudId)` to discover available link types (once per session)
2. Create links: `createIssueLink(cloudId, type: { name: "Blocks" }, outwardIssue: { key: "<BLOCKER>" }, inwardIssue: { key: "<BLOCKED>" })`
3. Document each link: `BLOCKER blocks BLOCKED — <reason>`

Identify the **critical path** — the longest chain of sequential dependencies.

### 2. Testing Strategy
- Which types of tests are needed (unit / integration / e2e)
- Coverage targets for new code
- Specific test scenarios to cover (happy path, edge cases, error paths)
- Commands to verify (`pytest`, `npm test`, etc.)
- Testing is not optional — every deliverable must have a testing plan

### 3. Documentation Plan
- What docs in `docs/` need creating or updating
- What memory entries to persist for future sessions
- What Jira comments to post
- Specify the audience for each doc artifact (ops team, future sessions, ticket reviewers)

### 4. Success Criteria
- Deterministic acceptance criteria for each deliverable
- Follow the standard format from the `success-criteria` rule
- Each criterion must be binary pass/fail and verifiable

### 5. Risk Assessment
- What could go wrong
- Mitigations for each risk
- External dependencies
- Fallback approaches if primary approach fails

## Posting plans

After the plan is drafted and confirmed with the user:
1. Post the full plan as a Jira comment on the relevant ticket using `addCommentToJiraIssue`
2. Structure as ordered phases with dependencies clearly marked
3. Include estimated effort where possible
4. Include the dependency graph and critical path

## Plan updates

If the plan changes during implementation:
1. Post an updated plan comment to Jira noting what changed and why
2. Update acceptance criteria if scope changed
