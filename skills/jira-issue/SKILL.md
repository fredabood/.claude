---
description: "Display a single Jira issue with full details including custom fields, links, and comments"
user_invocable: true
---

# /jira-issue

Display a single Jira issue with all relevant details, rendering custom fields by name.

## Usage

```
/jira-issue <KEY>
```

Example: `/jira-issue LAB-113`

## Steps

### Step 1: Write execution context marker

Write `.skill-execution-context.json` with: `{"skill": "jira-issue", "started_at": "<ISO8601>", "ticket_key": "<KEY>"}`

### Step 2: Fetch the issue

Use `mcp__claude_ai_Atlassian__getJiraIssue`:
- cloudId: `fredabood.atlassian.net`
- issueIdOrKey: the KEY from user input
- responseContentFormat: `markdown`

### Step 3: Display the issue

Render the issue with these sections:

#### Header

```
## <KEY>: <Summary>

**Status:** <status name> | **Priority:** <priority name> | **Type:** <issue type>
**Parent:** <parent key — parent summary> (if set)
**Created:** <date> | **Updated:** <date>
```

#### Labels (Taxonomy)

```
### Labels
**Work Pattern:** <pattern label from [scraper, agent, workflow, deployment, pipeline, migration, platform]>
**Infrastructure Layer:** <layer label from [L1-platform, L2-services, L3-framework, L4-domain]>
**Other:** <any non-taxonomy labels>
```

#### Description

Full markdown description from the issue. If the description contains an `## Acceptance Criteria` section, render it prominently.

#### Issue Links

```
### Issue Links

| Relationship | Key | Summary | Status |
|-------------|-----|---------|--------|
| blocks | LAB-200 | Some issue | To Do |
| is blocked by | LAB-100 | Other issue | Done |
| relates to | LAB-50 | Related issue | In Progress |
```

Show all link types. For "Blocks" links, indicate direction (blocks vs is blocked by). Show the linked issue's current status.

#### Custom Fields (by name)

Render populated custom fields using their human-readable names. Reference `.claude/rules/custom-fields.md` for the field ID to name mapping.

**Plan Fields** (show section only if any are populated):
```
### Plan
- **Jira Tracking** (customfield_10173): <value>
- **Testing Strategy** (customfield_10174): <value>
- **Documentation** (customfield_10175): <value>
- **Success Criteria** (customfield_10176): <value>
- **Risk Assessment** (customfield_10177): <value>
- **Sections Complete** (customfield_10190): <checked options>
```

**Verification Fields** (show section only if any are populated):
```
### Verification
- **Criteria Tested** (customfield_10178): <value>
- **Results Summary** (customfield_10179): <value>
- **Sections Complete** (customfield_10191): <checked options>
```

**Post-Mortem Fields** (show section only if any are populated):
```
### Post-Mortem
- **What Went Well** (customfield_10180): <value>
- **What Didn't Go Well** (customfield_10181): <value>
- **Lessons Learned** (customfield_10182): <value>
- **Metrics** (customfield_10183): <value>
- **Follow-Up Items** (customfield_10184): <value>
- **Sections Complete** (customfield_10192): <checked options>
```

**Doc Review Fields** (show section only if any are populated):
```
### Doc Review
- **Documentation** (customfield_10185): <value>
- **Memory Updates** (customfield_10186): <value>
```

**Agent Tracking Fields** (show section only if any are populated):
```
### Agent Tracking
- **Primary Agent** (customfield_10188): <value>
- **Assigned Agent** (customfield_10189): <value>
- **Agent Runtime** (customfield_10187): <value>
```

**Workflow Phase** (customfield_10193): Show if set.

Skip any section where all fields are null/empty.

#### Recent Comments

Show the last 3 comments, each truncated to 500 characters. Format:

```
### Recent Comments

**<author>** — <date>
> <comment body, truncated to 500 chars>

---
```

If no comments, display: "No comments."

### Step 4: Cleanup

Delete `.skill-execution-context.json`.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey, responseContentFormat)

## CloudId

Use `fredabood.atlassian.net` as the cloudId for all queries.
