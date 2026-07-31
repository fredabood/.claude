---
name: complete-task
description: Complete a task — run quality gates, add summary comment, set board Status to "Implementation Complete" (or close as completed)
user_invocable: true
---

# /complete-task

**Before any GitHub operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "complete-task", "started_at": "<current ISO8601 timestamp>", "ticket_key": "<issue key if known, null otherwise>"}`

Finish work on a GitHub issue. Verifies acceptance criteria, runs quality checks, posts a summary and post-mortem, and advances the issue — board Status "Implementation Complete" by default, or close as completed for terminal Done.

## Usage

```
/complete-task <#N | LAB-N | DRTY-N | RESORT-N>
```

(Historical `HL-N`/`DD-N` inputs still resolve: `HL-N` ≡ `LAB-N`, `DD-N` ≡ `DRTY-N`.)

Example: `/complete-task LAB-963`

Migrated keys (`LAB-*`, `DRTY-*`, `LEGACY-*`) resolve to repo+number via `public.github_migration_key_map` (see `/start-task`).

## Steps

### Step 1: Fetch the issue

Use `mcp__github__issue_read` (method: get) to retrieve current state, and `mcp__github__projects_get` to confirm board Status is "In Progress".

### Step 2: Run quality gates

Before completing, verify:
- All tests pass (run the project's test suite)
- No obvious security issues in changed files (grep for hardcoded secrets)
- Changed files are committed
- Test coverage on changed files has not decreased

**Hard gate:** Do not proceed if tests fail or security issues are found.

### Step 3: Verify acceptance criteria

Extract the `## Acceptance Criteria` task list from the issue **body**. For each criterion:
- Run the specified verification (test command from a `[pytest:...]` marker or `Tests pass:` text, file check, behavior walkthrough)
- Record pass/fail with evidence
- `[HUMAN-APPROVAL]` criteria require explicit user confirmation — do not self-approve

Generate and post a verification report comment using `mcp__github__add_issue_comment` (exact `##`/`###` markers per `.claude/rules/custom-fields.md`):

```markdown
## Verification Report

### Criteria Tested

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | <criterion> | PASS/FAIL | <how verified> |

### Results Summary
**Result:** ALL PASS / <N> FAILURES
```

Then tick the passing checkboxes in the issue body (`- [ ]` → `- [x]`) using `mcp__github__issue_write` (method: update).

**Hard gate:** Do not proceed if any criterion fails. List what needs fixing.

### Step 4: Generate summary

Collect:
- Files changed (`git diff --name-only` against the branch start)
- Key decisions made during implementation
- Any deviations from the original issue body
- Anything the next person should know
- Linked commits from the mirror: query `SELECT commit_short, repo, message FROM jira.commit_links WHERE issue_key = '<KEY>' ORDER BY committed_at` via `docker exec postgres-memory psql -U postgres -d agent_memory` (issue_key is the mirror key: `LAB-<n>`, `DRTY-<n>`, or `RESORT-<n>` — post-migration `<n>` = GitHub issue number, migrated issues keep their original keys) and include as a commits table in the summary

### Step 5: Add summary comment

Use `mcp__github__add_issue_comment` to post the summary in Markdown format.

### Step 6: Generate and post post-mortem

Generate a structured post-mortem following the `/post-mortem` workflow (heading marker must be `## Post-Mortem:`):

```markdown
## Post-Mortem: <KEY> — <Summary>

**Completed:** <date>
**Duration:** <time from In Progress to close>

### What Went Well
- <positive outcomes>

### What Didn't Go Well
- <issues, unexpected problems, time sinks>

### Lessons Learned
- <actionable insights>

### Metrics
- Files changed: <count>
- Commits: <count>
- Tests added/modified: <count>
- Acceptance criteria met: <X/Y>

### Follow-Up Items
- [ ] <remaining work>
```

Post using `mcp__github__add_issue_comment`. There are no custom fields on GitHub — the structured comment IS the canonical record (hooks and the mirror parse the `##`/`###` markers).

### Step 7: Advance status

**Preferred target:** board Status → "Implementation Complete" — use `mcp__github__projects_write` with the IDs from `.claude/rules/custom-fields.md`:
- Project `PVT_kwHOAM5y1M4BcqrU`, Status field `PVTSSF_lAHOAM5y1M4BcqrUzhXRxK4`, option "Implementation Complete" = `2eec8df1`

This leaves the issue open for `/review-ticket` (docs + memory + testing verification) before terminal close.

**Terminal Done (only when the user wants to skip the review stage or the review has already passed):** close the issue with `mcp__github__issue_write` — `state: closed`, `state_reason: completed`. Closing removes it from the board (D5 prune). Never use `state_reason: not_planned` here — that means Won't Do.

### Step 8: Check parent epic

If this issue is a sub-issue of an epic, check whether all siblings are closed: `mcp__github__issue_read` (method: get_sub_issues) on the parent, or `gh api repos/fredabood/<repo>/issues/<epic#>/sub_issues`. If all sub-issues are closed, note that the epic may be ready to close (as completed).

### Step 9: Persist lessons to memory

If the post-mortem contains significant lessons learned:
- Save to a memory file in the project memory directory
- Include enough context for future sessions to apply the lesson

### Step 10: Create follow-up issues

If follow-up items were identified in the post-mortem:
- Present them to the user
- Offer to create each as a new issue using `/create-ticket` logic

### Step 11: Output

Confirm completion with a brief summary (issue number, mirror key, new status, verification result).

## Required Tools

- `mcp__github__issue_read` (method: get, get_comments, get_sub_issues)
- `mcp__github__issue_write` (body checkbox updates; close with `state_reason: completed`)
- `mcp__github__projects_get` / `mcp__github__projects_write` (board Status)
- `mcp__github__add_issue_comment` (verification report, summary, post-mortem)
- `mcp__github__search_issues` / `mcp__github__sub_issue_write` — for follow-ups
- `gh api` — sub-issue/dependency readback; `docker exec postgres-memory psql` — commit links (Bash)

## Repos & Board

Repos: `fredabood/homelab`, `fredabood/dirtydata`. Board and Status option IDs: `.claude/rules/custom-fields.md`.

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
