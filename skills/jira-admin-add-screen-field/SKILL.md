---
name: jira-admin-add-screen-field
user_invocable: true
description: Add a custom field to a Jira project screen via Chrome DevTools — navigates project settings and adds the field
---

# /jira-admin-add-screen-field

Add a custom field to a Jira project's issue screen via the admin UI. Uses Chrome DevTools MCP to drive a real browser.

## Usage

```
/jira-admin-add-screen-field <project_key> <field_name>
```

Example: `/jira-admin-add-screen-field DRTY "Plan: Jira Tracking"`

For bulk operations, call this skill once per field. Or pass a comma-separated list and loop:
```
/jira-admin-add-screen-field DRTY "Plan: Jira Tracking,Plan: Testing Strategy,Plan: Documentation"
```

## Steps

### Step 1: Navigate to the project's screen configuration

Use `navigate_page` to open: `https://fredabood.atlassian.net/plugins/servlet/project-config/<project_key>/screens`

If that URL doesn't work, navigate via: Project Settings -> Screens.

Take a screenshot to confirm the screen configuration page loaded.

### Step 2: Identify the target screen

Take a screenshot. The screen scheme will show which screens are used for "Default", "Create", and "Edit" operations. Click on the default screen (the one used for viewing/editing issues).

### Step 3: Add the field

On the screen configuration page, look for an "Add field" button or a field search box at the bottom of the field list.

Type the `<field_name>` into the search/filter box. Select the matching field from the dropdown.

Click "Add" to add the field to the screen.

Take a screenshot to confirm the field now appears in the screen's field list.

### Step 4: Repeat for bulk operations

If multiple field names were provided (comma-separated), repeat Step 3 for each field without navigating away from the screen configuration page.

### Step 5: Verify

Take a final screenshot showing all added fields in the screen's field list.

Report what was added and which screen was modified.

## Important

- Screen changes take effect immediately — there is no "publish" step.
- If a field is already on the screen, the add operation will be a no-op or show a warning. Screenshot it and continue.
- Custom fields with IDs 10194 (Test Marker) and 10195 (Human Approval Required) belong on the Success Criterion screen only, not the default Task/Story screen.
