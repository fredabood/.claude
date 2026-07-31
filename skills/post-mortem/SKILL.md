---
name: post-mortem
description: Generate a structured post-mortem for a completed issue — what went well, what didn't, lessons learned, metrics
user_invocable: true
---

# /post-mortem

**Before any GitHub operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "post-mortem", "started_at": "<current ISO8601 timestamp>", "ticket_key": "<issue key if known, null otherwise>"}`

Generate and post a structured post-mortem for a GitHub issue. Captures outcomes, issues, lessons, and follow-up items.

## Usage

```
/post-mortem <#N | LAB-N | DRTY-N | RESORT-N>
```

(Historical `HL-N`/`DD-N` inputs still resolve: `HL-N` ≡ `LAB-N`, `DD-N` ≡ `DRTY-N`.)

Example: `/post-mortem LAB-963`

Migrated keys (`LAB-*`, `DRTY-*`, `LEGACY-*`) resolve to repo+number via `public.github_migration_key_map` (see `/start-task`).

## Steps

### Step 1: Fetch issue details

Use `mcp__github__issue_read` (method: get) and (method: get_comments) to retrieve the full issue including:
- Title, body, state (`state_reason` if closed), labels
- All comments (timeline of work — assignment, plan, milestones, verification)
- Created date, closed date

### Step 2: Gather context

- Query the mirror for linked commits: `SELECT commit_short, repo, message, committed_at FROM jira.commit_links WHERE issue_key = '<KEY>' ORDER BY committed_at` (via `docker exec postgres-memory psql -U postgres -d agent_memory`; `<KEY>` is the mirror key — `LAB-<n>`, `DRTY-<n>`, or `RESORT-<n>`; post-migration `<n>` = GitHub issue number, migrated issues keep their original keys)
- Fallback: `git log --grep="<KEY>" --oneline` if postgres unavailable
- Run `git log --grep="<KEY>" --stat` for files changed
- Review issue comments for the timeline of events (milestones, blockers, decisions)

### Step 3: Generate structured post-mortem

The heading marker must be exactly `## Post-Mortem:` — hooks and the mirror grep for it (see `.claude/rules/custom-fields.md`):

```markdown
## Post-Mortem: <KEY> — <Summary>

**Completed:** <date>
**Duration:** <time from In Progress to close>

### What Went Well
- <positive outcomes, smooth implementations, good decisions>

### What Didn't Go Well
- <issues encountered, unexpected problems, time sinks, blockers>

### Lessons Learned
- <actionable insights that should inform future work>

### Metrics
- Files changed: <count>
- Commits: <count>
- Tests added/modified: <count>
- Acceptance criteria met: <X/Y>

### Follow-Up Items
- [ ] <remaining work, tech debt, improvements identified>
```

Base the content on actual evidence from git history and issue comments — don't fabricate or guess. Duration: from the assignment comment / board Status "In Progress" timestamp to close (the mirror's `jira.status_transitions` has the history if needed).

### Step 4: Post to GitHub

Use `mcp__github__add_issue_comment` to post the full post-mortem on the issue. There are no custom fields on GitHub — the structured comment IS the canonical record (the mirror parses the `##`/`###` markers into its `pm_*` columns).

### Step 5: Persist to memory

If the post-mortem contains significant lessons learned (patterns to repeat, mistakes to avoid, architectural insights):
- Save to a memory file in the project memory directory
- Include enough context that a future session can apply the lesson without the original issue context

### Step 6: Create follow-up issues

If follow-up items were identified:
1. Present them to the user
2. Offer to create each as a new issue using `/create-ticket` logic
3. Link follow-up issues to the original — reference the original in the body (`Follow-up from <repo>#<n>`); if ordering matters, create blocked-by links via `gh api .../dependencies/blocked_by` (see `/create-ticket` Step 8)

## Required Tools

- `mcp__github__issue_read` (method: get, get_comments)
- `mcp__github__add_issue_comment`
- `mcp__github__issue_write` / `mcp__github__sub_issue_write` — for follow-ups
- `gh api` — dependency links; `docker exec postgres-memory psql` — commit links (Bash)

## Repos & Board

Repos: `fredabood/homelab`, `fredabood/dirtydata`. Board and Status option IDs: `.claude/rules/custom-fields.md`.

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
