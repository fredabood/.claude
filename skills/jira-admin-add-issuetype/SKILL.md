---
name: jira-admin-add-issuetype
user_invocable: true
description: Add an issue type to a Jira project's issue type scheme via Chrome DevTools
---

# /jira-admin-add-issuetype

Add an issue type to a Jira project's issue type scheme via the admin UI. Uses Chrome DevTools MCP to drive a real browser.

## Usage

```
/jira-admin-add-issuetype <project_key> <issue_type_name>
```

Example: `/jira-admin-add-issuetype DRTY "Success Criterion"`

## Steps

### Step 1: Navigate to the project's issue type configuration

Use `navigate_page` to open: `https://fredabood.atlassian.net/jira/settings/projects/<project_key>/issuetypes`

Take a screenshot to confirm the page loaded. If redirected to a login page, pause and ask the user to authenticate.

### Step 2: Open the issue type scheme editor

Take a screenshot to see the current issue types. Look for an "Actions" menu, gear icon, or "Edit issue types" link.

Click to open the issue type scheme editor. This usually shows two columns: "Available issue types" on the left and "Current scheme" on the right.

### Step 3: Add the issue type

In the "Available issue types" panel, locate `<issue_type_name>` (e.g., "Success Criterion").

Either:
- Drag it from the left panel to the right panel, OR
- Click a "+" or "Add" button next to it

Take a screenshot to confirm the issue type now appears in the "Current scheme" list.

### Step 4: Save

Click "Save" to apply the scheme change.

Take a screenshot to confirm the save succeeded and the issue type now appears in the project's issue type list.

### Step 5: Verify programmatically

After the UI change, verify via the Jira API:
```
mcp__claude_ai_Atlassian__getJiraProjectIssueTypesMetadata(projectIdOrKey="<project_key>")
```

Confirm the new issue type appears in the response.

## Important

- If the issue type scheme is shared across multiple projects, the change will affect all projects using that scheme. The editor may warn about this — screenshot the warning and ask the user whether to proceed or create a dedicated scheme first.
- Issue type scheme changes take effect immediately after save.
