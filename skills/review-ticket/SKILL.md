---
description: Verify acceptance criteria for a ticket — run tests, check conditions, post verification report to Jira
user_invocable: true
---

# /review-ticket

**Before any Jira operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "review-ticket", "started_at": "<current ISO8601 timestamp>", "ticket_key": "<ticket key if known, null otherwise>"}`

Verify all acceptance criteria for a Jira ticket before completion. Runs tests, checks conditions, and posts a verification report.

## Usage

```
/review-ticket <ISSUE-KEY>
```

Example: `/review-ticket PROJ-123`

## Steps

### Step 1: Fetch ticket

Use `getJiraIssue` to retrieve the ticket description and all comments.

### Step 2: Extract acceptance criteria

Parse the `Acceptance Criteria` section from the ticket description. If no criteria exist:
1. Check comments for criteria posted later
2. If still none found, report: "No acceptance criteria found. Run `/start-task` to draft criteria before reviewing."

### Step 3: Verify each criterion

For each criterion, determine the verification method and execute it:

| Criterion type | Verification method |
|---|---|
| Test-based (`Tests pass: <command>`) | Run the command, capture pass/fail output |
| File-based (file exists, config present) | Check file existence and content |
| Behavior-based (feature works as described) | Walk through verification steps, document evidence |
| Security (no regressions) | Run security checks on changed files |
| Documentation (docs updated) | Verify referenced docs exist and are current |

### Step 4: Generate verification report

```markdown
## Acceptance Criteria Verification: <KEY>

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | <criterion text> | PASS | <how verified, command output summary> |
| 2 | <criterion text> | FAIL | <what failed, expected vs actual> |

**Result:** ALL PASS / <N> FAILURES

### Details
<expanded evidence for any non-trivial verifications>
```

### Step 5: Populate verification fields

Use `editJiraIssue` to write verification data to custom fields:

```
editJiraIssue(issueIdOrKey, fields={
    "customfield_10178": "<all criteria tested — list from report>",
    "customfield_10179": "<results summary — X/Y pass, any failures>",
    "customfield_10191": [
        {"id": "10135"},   // Criteria Tested
        {"id": "10136"},   // Results Posted
        // Add {"id": "10137"} (All Pass) only if ALL criteria passed
    ]
})
```

Field IDs reference `.claude/rules/custom-fields.md`.

### Step 6: Post to Jira

Use `addCommentToJiraIssue` to post the verification report on the ticket.

### Step 7: Gate result

- **All pass:** Confirm the ticket is ready for `/complete-task`.
- **Any fail:** List what needs fixing. Do not proceed to completion. Suggest specific actions to address each failure.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
