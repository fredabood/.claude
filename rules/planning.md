---
description: Planning mode behavior — every plan must include issue tracking, testing strategy, documentation plan, success criteria, and risk assessment
globs:
  - "**/*"
---

# Planning — Structured Design Requirements

> Invoke `/workflow` for Phase 3 (plan posting) with deterministic hook enforcement — code edits are blocked until the plan is posted.

When asked to plan, design, or architect a solution, the plan **must** include all five sections below. Plans are not just conversation output — they are posted as a comment on the relevant GitHub issue under the `## Implementation Plan` marker (see `.claude/rules/custom-fields.md` for the structured comment vocabulary).

## Required plan sections

### 1. Issue Tracking Plan

#### Decomposition evaluation

Before creating issues, evaluate whether the work should be decomposed:

- **Multiple codebase areas:** Does the work touch independent parts of the system?
- **Independent acceptance criteria:** Can groups of criteria be verified in isolation?
- **Phase boundaries:** Is there a natural split between setup/infrastructure and feature work?
- **Session scope:** Would the work take more than one session?
- **Mixed types:** Does it include both bug fixes and features, or both infrastructure and user-facing changes?

If two or more apply, decompose into multiple issues. Use sub-issues of a parent issue when pieces are parts of one story; independent linked issues when each has standalone value.

#### Issue structure

- What issues to create (in which repo — `fredabood/homelab` or `fredabood/dirtydata`)
- Parent-issue membership: which parent issue they become sub-issues of (`mcp__github__sub_issue_write`)
- Taxonomy labels per `.claude/rules/label-taxonomy.md`

#### Dependency mapping

For each pair of issues where one must complete before another can start:

1. Create a blocked-by link (no MCP tool — use `gh api` with the pinned version header):
   ```bash
   gh api -X POST repos/fredabood/<repo>/issues/<BLOCKED#>/dependencies/blocked_by \
     -H "X-GitHub-Api-Version: 2026-03-10" -F issue_id=<BLOCKER-database-id>
   ```
   (Blocker's database id: `gh api repos/fredabood/<repo>/issues/<BLOCKER#> --jq .id`)
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
- What issue comments to post
- Specify the audience for each doc artifact (ops team, future sessions, issue reviewers)

### 4. Success Criteria
- Deterministic acceptance criteria for each deliverable
- Follow the standard format from the `success-criteria` rule (task list in the issue body)
- Each criterion must be binary pass/fail and verifiable

### 5. Risk Assessment
- What could go wrong
- Mitigations for each risk
- External dependencies
- Fallback approaches if primary approach fails

## Posting plans

After the plan is drafted and confirmed with the user:
1. Post the full plan as an issue comment using `mcp__github__add_issue_comment`, starting with the `## Implementation Plan` marker (this is what the Planned check greps for)
2. Structure as ordered phases with dependencies clearly marked
3. Include estimated effort where possible
4. Include the dependency graph and critical path

## Plan updates

If the plan changes during implementation:
1. Post an updated plan comment (again under `## Implementation Plan`) noting what changed and why
2. Update the acceptance criteria task list in the issue body if scope changed
