---
description: Planning mode behavior — every plan must include Plane tracking, testing strategy, documentation plan, success criteria, and risk assessment
globs:
  - "**/*"
---

# Planning — Structured Design Requirements

When asked to plan, design, or architect a solution, the plan **must** include all five sections below. Plans are not just conversation output — they are posted to the relevant Plane work item.

## Required plan sections

### 1. Plane Tracking Plan

#### Decomposition evaluation

Before creating work items, evaluate whether the work should be decomposed:

- **Multiple codebase areas:** Does the work touch independent parts of the system?
- **Independent acceptance criteria:** Can groups of criteria be verified in isolation?
- **Phase boundaries:** Is there a natural split between setup/infrastructure and feature work?
- **Session scope:** Would the work take more than one session?
- **Mixed types:** Does it include both bug fixes and features, or both infrastructure and user-facing changes?

If two or more apply, decompose into multiple work items. Use sub-items when pieces are parts of one story; independent linked items when each has standalone value.

#### Work item structure

- What work items to create (with type as appropriate)
- How they relate to existing epics/modules
- Cycle (sprint) assignment (if applicable)

#### Dependency mapping

For each pair of work items where one must complete before another can start:

1. Create relation: `mcp__plane__create_work_item_relation(work_item_id=<BLOCKER>, related_issue=<BLOCKED>, relation_type="blocks")`
2. Document each link: `BLOCKER blocks BLOCKED — <reason>`

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
- What Plane comments to post
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
1. Post the full plan as a Plane comment on the relevant work item using `mcp__plane__create_work_item_comment`
2. Structure as ordered phases with dependencies clearly marked
3. Include estimated effort where possible
4. Include the dependency graph and critical path

## Plan updates

If the plan changes during implementation:
1. Post an updated plan comment to Plane noting what changed and why
2. Update acceptance criteria if scope changed
