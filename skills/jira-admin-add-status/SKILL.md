---
name: jira-admin-add-status
user_invocable: true
description: Add a status to a Jira project workflow via Chrome DevTools — navigates the admin UI, adds the status, does NOT publish
---

# /jira-admin-add-status

Add a named status to a Jira project's workflow via the admin UI. Uses Chrome DevTools MCP to drive a real browser. Does NOT publish the workflow — use `/jira-admin-publish-workflow` separately after all statuses are added.

## Usage

```
/jira-admin-add-status <project_key> <status_name> <status_category>
```

Example: `/jira-admin-add-status DRTY "Implementation Complete" "In progress"`

## Steps

### Step 1: Navigate to the workflow editor

Use `navigate_page` to open: `https://fredabood.atlassian.net/jira/settings/projects/<project_key>/workflows`

Take a screenshot to confirm the page loaded. If a login prompt appears, pause and ask the user to authenticate manually in the browser window.

### Step 2: Open the project's active workflow

Take a screenshot to identify the active workflow name. Click the workflow name or the "Edit" pencil icon to open the workflow editor in diagram mode.

Take a screenshot to confirm the workflow diagram is visible.

### Step 3: Add the new status

Click the "Add status" button (usually in the toolbar above the diagram or via a "+" icon).

A dialog will appear. Fill in:
- **Name:** the `<status_name>` parameter
- **Category:** select the `<status_category>` parameter from the dropdown (options: "To do", "In progress", "Done")

Take a screenshot to confirm the dialog is filled correctly.

Click "Add" or "Save" to add the status to the workflow.

### Step 4: Add transitions

After the status appears on the diagram, add the required transitions:
- If the status category is "In progress": add a transition FROM the previous in-progress status TO this new status (e.g., "In Progress" -> "Implementation Complete")
- If the status category is "Done": add a global transition from any status to this one
- If the status category is "To do": add a global transition from any non-terminal status

Use `click` on the source status, drag to the new status, or use the "Add transition" dialog if available.

### Step 5: Verify

Take a screenshot of the final diagram showing the new status and its transitions.

Report what was added and remind the user that the workflow is NOT yet published. Use `/jira-admin-publish-workflow` to publish when ready.

## Important

- This skill adds statuses to the draft workflow only. Publishing is a separate, destructive operation.
- If the workflow is shared across multiple projects, the editor may warn about this. Screenshot the warning and ask the user whether to proceed or copy the workflow first.
- Atlassian admin pages require a "secure administration session" that expires after ~10 minutes. If re-auth is needed, the screenshot step will catch it.
