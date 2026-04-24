---
name: jira-admin-publish-workflow
user_invocable: true
description: Publish a Jira workflow after edits — includes mandatory visual confirmation before the destructive publish step
---

# /jira-admin-publish-workflow

Publish a Jira project workflow after edits have been made (e.g., after `/jira-admin-add-status` has added new statuses). This is a DESTRUCTIVE operation — once published, the workflow changes are live and affect all issues in the project.

## Usage

```
/jira-admin-publish-workflow <project_key>
```

Example: `/jira-admin-publish-workflow DRTY`

## Steps

### Step 1: Navigate to the workflow editor

Use `navigate_page` to open: `https://fredabood.atlassian.net/jira/settings/projects/<project_key>/workflows`

Take a screenshot to confirm the page loaded.

### Step 2: Open the draft workflow

Click the workflow that has unpublished changes (it may show a "Draft" badge or a warning indicator).

Take a screenshot of the workflow diagram showing ALL statuses and transitions. This is the pre-publish verification image.

### Step 3: MANDATORY USER CONFIRMATION

Show the user the screenshot and explicitly ask:

> "This workflow is about to be published for project <project_key>. The screenshot above shows the current draft with all statuses and transitions. Publishing is irreversible — all issues in the project will immediately use this workflow. Do you want to proceed?"

**DO NOT click Publish until the user explicitly confirms.** This is a hard gate, not a soft suggestion.

### Step 4: Publish

After user confirmation, click the "Publish" button.

If a confirmation dialog appears, take a screenshot and click "Publish" again to confirm.

### Step 5: Verify

Take a screenshot of the published workflow (should no longer show "Draft" badge).

Verify programmatically:
```
mcp__claude_ai_Atlassian__getTransitionsForJiraIssue(issueIdOrKey="<project_key>-1")
```

Confirm the new transitions appear in the response. Report the full list of available transitions.

## Important

- NEVER skip Step 3 (user confirmation). This is the only destructive Jira admin skill.
- If the workflow is shared with other projects, the publish dialog will list affected projects. Screenshot this and include it in the confirmation prompt.
- If anything looks wrong in the pre-publish screenshot (missing statuses, broken transitions), abort and ask the user to review.
