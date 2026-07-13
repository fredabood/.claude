---
description: "Display a single GitHub issue with full details — state, board status, labels, sub-issues, dependencies, and comments"
user_invocable: true
---

# /jira-issue

Display a single GitHub issue with all relevant details. (Directory name kept as
`jira-issue` for invocation compatibility — the tracker is GitHub Issues; the
postgres mirror retains the `jira.*` schema name.)

## Usage

```
/jira-issue <KEY>
```

Accepted key formats:

| Input | Meaning |
|-------|---------|
| `LAB-963` | `fredabood/homelab` — post-migration keys (n ≥ 941): issue #n directly; migrated `LAB-*` (n ≤ 286) and `LEGACY-*` resolve via the mirror key map |
| `DRTY-45` | `fredabood/dirtydata` — same rule (post-migration: issue #n; migrated: mirror key map) |
| `RESORT-12` | `fredabood/9215resort` issue #12 (transfer map: `public.resort_transfer_key_map`) |
| `HL-123` / `DD-45` | deprecated (LAB-963) — resolve as `HL-n` ≡ `LAB-n`, `DD-n` ≡ `DRTY-n` |
| `#123` or `123` | issue number in the repo inferred from cwd (homelab repo root → homelab; `submodules/dirtydata/` → dirtydata; default homelab) |

Example: `/jira-issue LAB-113`

## Steps

### Step 1: Write execution context marker

Write `.skill-execution-context.json` with: `{"skill": "jira-issue", "started_at": "<ISO8601>", "ticket_key": "<KEY>"}`

### Step 2: Resolve the key to (repo, number)

- Post-migration keys → number is the issue number: `LAB-<n>` (n ≥ 941) → (`fredabood/homelab`, n), `DRTY-<n>` → (`fredabood/dirtydata`, n), `RESORT-<n>` → (`fredabood/9215resort`, n). Deprecated `HL-<n>`/`DD-<n>` ≡ `LAB-<n>`/`DRTY-<n>`. `#<n>` → repo from context.
- Migrated keys (`LAB-*` ≤ 286, `DRTY-*`, `LEGACY-*`) → resolve via the mirror (works for any key):

```bash
docker exec postgres-memory psql -U postgres -d agent_memory -tA -c \
  "SELECT gh_repo, gh_number FROM jira.issues WHERE issue_key = '<KEY>'"
```

If no row is found, tell the user the key is unknown and stop.

### Step 3: Fetch the issue

Use `mcp__github__issue_read` with owner `fredabood`, repo, and issue number:

- method `get` → state, `state_reason`, title, body, labels, assignees, timestamps
- method `get_comments` → comments
- method `get_sub_issues` → sub-issues (if any — an issue with sub-issues is an epic)

### Step 4: Board status (open issues only)

If the issue is **open**, read its board Status from the "Homelab Work" Projects v2
board (user `fredabood`, project number 1) via `mcp__github__projects_get`. Board
statuses: `Backlog`, `In Progress`, `Implementation Complete`, `Review Complete`,
`Deferred`. If the issue is **closed**, its status is terminal: `Done`
(`state_reason: completed`) or `Won't Do` (`state_reason: not_planned`) — closed
issues are not on the board.

Fallback: the mirror's `status` column on `jira.issues` carries the same value.

### Step 5: Dependencies

Blockers (issues this one waits on):

```bash
gh api repos/fredabood/<repo>/issues/<n>/dependencies/blocked_by \
  -H "X-GitHub-Api-Version: 2026-03-10"
```

For the reverse direction (what this issue blocks) and `Relates` links (mirror-only),
query the mirror — `source_key` = blocker, `target_key` = blocked:

```bash
docker exec postgres-memory psql -U postgres -d agent_memory -c "
SELECT l.link_type,
       CASE WHEN l.source_key = '<MIRROR_KEY>' THEN 'blocks/relates to' ELSE 'is blocked by/relates to' END AS direction,
       CASE WHEN l.source_key = '<MIRROR_KEY>' THEN l.target_key ELSE l.source_key END AS other_key,
       i.summary, i.status
FROM jira.issue_links l
JOIN jira.issues i ON i.issue_key = CASE WHEN l.source_key = '<MIRROR_KEY>' THEN l.target_key ELSE l.source_key END
WHERE '<MIRROR_KEY>' IN (l.source_key, l.target_key)"
```

`<MIRROR_KEY>` is the mirror key (`LAB-<n>`/`DRTY-<n>`/`RESORT-<n>`; migrated issues keep their
original `LAB-*`/`DRTY-*`/`LEGACY-*` keys — `jira.gh_issue_key('<repo>', <n>)` resolves it from repo+number).

### Step 6: Display the issue

#### Header

```
## <KEY>: <Title>  (fredabood/<repo>#<n>)

**State:** open|closed (<state_reason if closed>) | **Board Status:** <status>
**Parent:** <parent issue, if this is a sub-issue> | **Epic:** yes, <k> sub-issues (if it has sub-issues)
**Created:** <date> | **Updated:** <date>
<html_url>
```

#### Labels (Taxonomy)

```
### Labels
**Work Pattern:** <one of: scraper, agent, workflow, deployment, pipeline, migration, platform>
**Infrastructure Layer:** <one of: L1-platform, L2-services, L3-framework, L4-domain>
**Other:** <any non-taxonomy labels>
```

#### Body

Full markdown body. If it contains an `## Acceptance Criteria` task list, render it
prominently with checked/unchecked state.

#### Sub-issues (if any)

```
### Sub-issues
| # | Title | State |
|---|-------|-------|
```

#### Dependencies

```
### Dependencies
| Relationship | Key | Summary | Status |
|-------------|-----|---------|--------|
| is blocked by | LAB-100 | Other issue | Done |
| blocks | LAB-200 | Some issue | Backlog |
| relates to | LAB-50 | Related issue | In Progress |
```

Flag any open blocker (status not Done/Won't Do) with a warning.

#### Structured comments

Scan comments for the structured markers from `.claude/rules/custom-fields.md`
(`## Implementation Plan`, `## Verification Report`, `## Post-Mortem`, `## Doc Review`,
`Assigned Agent:`). Show which exist, each with author + date. For **migrated** issues,
the historical field content lives in mirror columns (`plan_*`, `verification_*`, `pm_*`,
`doc_review_*`, `assigned_agent`, …) — surface any populated ones under the matching heading.

#### Recent Comments

Show the last 3 comments, each truncated to 500 characters:

```
### Recent Comments

**<author>** — <date>
> <comment body, truncated to 500 chars>

---
```

If no comments, display: "No comments."

### Step 7: Cleanup

Delete `.skill-execution-context.json`.

## Required tools

- `mcp__github__issue_read` (get, get_comments, get_sub_issues)
- `mcp__github__projects_get` (board Status for open issues)
- `gh api repos/fredabood/<repo>/issues/<n>/dependencies/blocked_by` (blockers)
- `docker exec postgres-memory psql -U postgres -d agent_memory` (key map, reverse/Relates links, migrated field content — READ ONLY)
