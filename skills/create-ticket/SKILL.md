---
name: create-ticket
description: Create a structured GitHub issue with acceptance criteria, duplicate detection, and epic linking
user_invocable: true
---

# /create-ticket

**Before any GitHub operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "create-ticket", "started_at": "<current ISO8601 timestamp>", "ticket_key": null}`

Create a well-structured GitHub issue with acceptance criteria, after checking for duplicates.

## Usage

```
/create-ticket "<description>"
/create-ticket "<description>" --epic <#N | LAB-N | DRTY-N | RESORT-N>
/create-ticket "<description>" --type Bug
```

## Steps

### Step 1: Search for existing issues

Query GitHub for related issues to avoid duplicates:
```
mcp__github__search_issues(query: "repo:fredabood/<repo> is:issue is:open <keywords>")
```

Optionally widen to closed issues (`is:issue <keywords>`) if the work may already be done. For analytical sweeps across both repos, the mirror works too:
```
docker exec postgres-memory psql -U postgres -d agent_memory -c \
  "SELECT issue_key, summary, status FROM jira.issues WHERE summary ILIKE '%<keyword>%' AND status_category != 'Done' ORDER BY created_at DESC LIMIT 20"
```

If potential duplicates found, present them and ask the user to confirm this is new work.

### Step 2: Evaluate decomposition

Assess whether the described work should be multiple issues:

- **Multiple codebase areas:** Independent parts of the system?
- **Independent verification:** Acceptance criteria groupable into independently verifiable sets?
- **Phase boundaries:** Setup/infrastructure separate from feature work?
- **Session scope:** More than one session of effort?
- **Mixed types:** Bugs + features, or infrastructure + user-facing?

If 2+ criteria apply:
1. Present the proposed decomposition: each issue with title, shape (bug label / sub-issue of an epic / standalone), and which acceptance criteria it carries
2. If a work pattern was detected in Step 2.5 and decomposition is warranted, offer the standard decomposition template from `.claude/rules/label-taxonomy.md` (e.g., scraper → 4-step template). Each step becomes a separate issue with blocked-by links between them.
3. Ask user to confirm or adjust
4. If confirmed, create each issue individually (following Steps 3-9 for each)
5. After all created, proceed to dependency linking step

If not warranted, proceed with a single issue.

### Step 2.5: Detect work pattern

Scan the user's description against the keyword hints in `.claude/rules/label-taxonomy.md`:

| Pattern | Keywords |
|---|---|
| `scraper` | scrape, crawl, fetch, ingest, connector, API client |
| `agent` | agent, AI, LLM, tool-use, autonomous |
| `workflow` | n8n, workflow, automation, schedule, trigger |
| `deployment` | deploy, service, stack, container, Caddy route |
| `pipeline` | pipeline, ETL, medallion, transform, schema |
| `migration` | migrate, consolidate, export, import, decommission |
| `platform` | infrastructure, Docker, security, networking, monitoring |

If a pattern is detected:
1. Present: "Detected work pattern: **{pattern}**. Correct?"
2. If the user overrides, use their choice
3. If decomposition is warranted (Step 2), offer the standard template from the label-taxonomy rule

If no pattern is detected, ask the user to choose from the 7 options.

### Step 2.6: Assign infrastructure layer

Determine the layer from the target repo and content:

- **Single-domain work** (consumed by exactly one domain project) → `L4-domain` automatically
- **Shared/platform work** (homelab repo) → infer from content:
  - Docker, Caddy, DNS, networking, security, backup → `L1-platform`
  - Service names (PostgreSQL, Ollama, n8n, Grafana, etc.) → `L2-services`
  - Framework, primitives, scraper framework, agent runtime → `L3-framework`

Present: "Infrastructure layer: **{layer}**. Correct?"
User can always override.

### Step 3: Determine issue shape and target repo

GitHub has no issue types — shape is expressed with labels and structure:

- **Bug** — something is broken → add the `bug` label
- **Epic** — container for decomposed work → an issue with sub-issues (epic-ness is derived)
- **Sub-issue** — part of a larger epic (requires parent; linked in Step 8)
- **Everything else** — a plain issue (the mirror shows it as `Task`)

Target repo routing (per CLAUDE.md §7 placement tree):
- Zero domain consumers (generic infra) → `fredabood/homelab` (L1/L2)
- One domain consumer → that domain's repo (e.g., `fredabood/dirtydata` for DirtyData work, L4)
- Many domain consumers → `fredabood/homelab` as L3 framework

Infer from the description or ask the user if ambiguous.

### Step 4: Draft the issue

Structure the issue **body** with these sections. Acceptance criteria must be a native task list in the body (not a comment) — the body is editable and renders progress:

```markdown
**Title:** <under 80 characters>
**Taxonomy:** `{pattern}` / `{layer}`

## Context
<Why this work is needed — the problem or opportunity>

## Scope
<What specifically will be done>

## Acceptance Criteria
- [ ] <Specific verifiable condition>
- [ ] Tests pass: `<command>`
- [ ] No security regressions
- [ ] Documentation updated (if applicable)

## Out of Scope
<What is explicitly not included>

## Technical Notes
<Implementation hints, relevant files, dependencies>
**Primary Agent:** <agent-id from taxonomy routing table in .claude/rules/label-taxonomy.md>
```

Criterion markers (see `.claude/rules/custom-fields.md`):
- If a criterion maps to a specific test command/marker, prepend it: `- [ ] [pytest:test_foo] <condition>`
- If a criterion is subjective, documentation-related, or requires human judgment, prepend `[HUMAN-APPROVAL]`: `- [ ] [HUMAN-APPROVAL] <condition>`

### Step 5: Add HITL review criteria

Always append two human-in-the-loop criteria to the Acceptance Criteria task list:

```markdown
- [ ] [HUMAN-APPROVAL] Documentation updates reviewed
- [ ] [HUMAN-APPROVAL] Memory/vault updates reviewed
```

These ensure documentation and memory persistence are explicitly verified by a human before the issue is closed.

### Step 6: Present for confirmation

Show the draft to the user. Wait for approval before creating.

### Step 7: Create on GitHub

Use `mcp__github__issue_write` (method: create) against the target repo. Include:
- Title, body
- Labels: taxonomy labels from Steps 2.5/2.6 (`[detected_pattern, detected_layer]`), plus `bug` if applicable, plus optional `source:` label

Do NOT add the issue to the board manually — the n8n `github-webhook-receiver` auto-adds new issues to the "Homelab Work" board with `Status=Backlog`.

The mirror key is `LAB-<n>` (homelab), `DRTY-<n>` (dirtydata), or `RESORT-<n>` (9215resort), where `<n>` is the new issue number.

### Step 8: Link to parent and dependencies

**Epic link:** If an epic was specified, use `mcp__github__sub_issue_write` to add the new issue as a sub-issue of the epic.

**Dependency links:** There is no MCP dependencies tool — use `gh api` with the pinned version header. The BLOCKED issue declares its BLOCKER, and `issue_id` is the blocker's **database id** (not its number):

```bash
# Get the blocker's database id:
gh api repos/fredabood/<repo>/issues/<BLOCKER#> --jq .id

# Blocked by an existing issue (new issue waits):
gh api -X POST repos/fredabood/<repo>/issues/<NEW#>/dependencies/blocked_by \
  -H "X-GitHub-Api-Version: 2026-03-10" -F issue_id=<blocker-db-id>

# Blocks an existing issue (existing issue waits on the new one):
gh api -X POST repos/fredabood/<repo>/issues/<EXISTING#>/dependencies/blocked_by \
  -H "X-GitHub-Api-Version: 2026-03-10" -F issue_id=<new-issue-db-id>
```

Cross-repo dependencies work. Direction: **the blocker must finish first; the blocked issue waits.**

**Decomposed issues:** If multiple issues were created, create blocked-by links between them to express ordering (earlier phases block later phases).

### Step 9: Standalone criterion tracking (optional)

The old Success Criterion subtask type is gone. If an individual acceptance criterion needs standalone tracking (own assignee, own timeline), convert that task-list item to a sub-issue using `mcp__github__sub_issue_write` with the new issue as parent. Otherwise, the body task list is the canonical checklist — no child issues needed.

### Step 10: Output

Display:
- Issue number, mirror key (`LAB-<n>` / `DRTY-<n>` / `RESORT-<n>`), and title
- Link to the issue (`html_url`)
- Acceptance criteria summary
- Epic/sub-issue links created
- Dependency links created: `BLOCKER blocks BLOCKED`
- Note that the board will show it under `Backlog` shortly (webhook auto-add)

## Required Tools

- `mcp__github__search_issues` (duplicate detection)
- `mcp__github__issue_write` (create)
- `mcp__github__sub_issue_write` (epic membership, standalone criteria)
- `mcp__github__issue_read` (readback)
- `gh api repos/fredabood/<repo>/issues/<n>/dependencies/blocked_by` — dependency links (Bash)

## Repos & Board

Repos: `fredabood/homelab`, `fredabood/dirtydata`. Board "Homelab Work" IDs: see `.claude/rules/custom-fields.md` (new issues are auto-added as Backlog — no board write needed here).

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
